import { serve } from "https://deno.land/std@0.168.0/http/server.ts"

// CORS headers for preflight requests
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const { url, metadata } = await req.json()

    if (!url) {
      return new Response(
        JSON.stringify({ error: 'URL is required' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    console.log(`Parsing resume from: ${url}`)

    // Download PDF
    const pdfResponse = await fetch(url)
    if (!pdfResponse.ok) {
      throw new Error(`Failed to download PDF: ${pdfResponse.status}`)
    }

    const pdfBuffer = await pdfResponse.arrayBuffer()

    // Import PDF.js from CDN
    const pdfjsLib = await import('https://cdn.jsdelivr.net/npm/pdfjs-dist@3.11.174/+esm')

    // Set worker source (required for PDF.js)
    pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdn.jsdelivr.net/npm/pdfjs-dist@3.11.174/build/pdf.worker.min.js'

    // Load PDF document
    const loadingTask = pdfjsLib.getDocument({ data: pdfBuffer })
    const pdf = await loadingTask.promise

    // Extract text from all pages
    let fullText = ''
    for (let i = 1; i <= pdf.numPages; i++) {
      const page = await pdf.getPage(i)
      const textContent = await page.getTextContent()
      const pageText = textContent.items.map((item: any) => item.str).join(' ')
      fullText += pageText + '\n'
    }

    console.log(`Extracted ${fullText.length} characters of text`)

    // Parse resume structure (basic MVP implementation)
    const parsedData = parseResumeText(fullText)

    return new Response(
      JSON.stringify({
        success: true,
        data: parsedData,
        metadata: {
          ...metadata,
          parsed_at: new Date().toISOString(),
          text_length: fullText.length
        }
      }),
      {
        status: 200,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    )

  } catch (error) {
    console.error('Error parsing resume:', error)
    return new Response(
      JSON.stringify({
        error: error.message,
        success: false
      }),
      {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    )
  }
})

/**
 * Parse resume text into structured data
 * This is a basic MVP implementation - can be improved later
 */
function parseResumeText(text: string): any {
  const lines = text.split('\n').filter(line => line.trim())

  // Extract basic contact info (first few lines typically)
  const name = extractName(lines)
  const email = extractEmail(text)
  const phone = extractPhone(text)
  const location = extractLocation(text)
  const linkedin = extractLinkedIn(text)

  // Extract sections
  const summary = extractSection(text, ['summary', 'profile', 'objective', 'about'])
  const experiences = extractExperiences(text)
  const education = extractEducation(text)
  const skills = extractSkills(text)

  return {
    name: name || 'Resume Applicant',
    email: email || '',
    phone: phone || '',
    location: location || '',
    linkedin: linkedin || '',
    summary: summary || '',
    experiences: experiences,
    education: education,
    skills: skills,
    metadata: {
      source: 'supabase-edge-parser',
      version: '1.0.0'
    }
  }
}

function extractName(lines: string[]): string {
  // Typically the first non-empty line
  return lines[0]?.trim() || ''
}

function extractEmail(text: string): string {
  const emailRegex = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/
  const match = text.match(emailRegex)
  return match ? match[0] : ''
}

function extractPhone(text: string): string {
  const phoneRegex = /(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}/
  const match = text.match(phoneRegex)
  return match ? match[0] : ''
}

function extractLocation(text: string): string {
  // Look for city, state patterns
  const locationRegex = /([A-Z][a-z]+,\s*[A-Z]{2})|([A-Z][a-z]+\s*,\s*[A-Z][a-z]+)/
  const match = text.match(locationRegex)
  return match ? match[0] : ''
}

function extractLinkedIn(text: string): string {
  const linkedInRegex = /(https?:\/\/)?(www\.)?linkedin\.com\/in\/[\w-]+/i
  const match = text.match(linkedInRegex)
  return match ? match[0] : ''
}

function extractSection(text: string, headers: string[]): string {
  for (const header of headers) {
    const regex = new RegExp(`${header}[:\\s]+([^]*?)(?=\\n\\n|$)`, 'i')
    const match = text.match(regex)
    if (match && match[1]) {
      return match[1].trim().substring(0, 500) // Limit to 500 chars
    }
  }
  return ''
}

function extractExperiences(text: string): any[] {
  const experiences: any[] = []

  // Look for "Experience" or "Work History" section
  const expSectionRegex = /(experience|work history|employment)[:\s]+([^]*?)(?=(education|skills|certifications|$))/i
  const expMatch = text.match(expSectionRegex)

  if (!expMatch) return []

  const expText = expMatch[2]

  // Split by common job entry patterns (company names often in all caps or bold)
  const entries = expText.split(/\n\n+/)

  for (const entry of entries.slice(0, 5)) { // Limit to 5 experiences
    if (entry.trim().length < 20) continue

    const lines = entry.split('\n').filter(l => l.trim())
    if (lines.length < 2) continue

    // Basic parsing: first line = role, second = company, rest = bullets
    const role = lines[0]?.trim() || 'Position'
    const company = lines[1]?.trim() || 'Company'

    // Extract bullets (lines starting with • or - or containing action verbs)
    const bullets = lines.slice(2)
      .filter(l => l.length > 10)
      .map(l => l.replace(/^[•\-*]\s*/, '').trim())
      .filter(l => l.length > 0)

    experiences.push({
      role,
      company,
      duration: 'Date range not parsed',
      responsibilities: bullets.length > 0 ? bullets : ['Responsibilities not parsed']
    })
  }

  return experiences
}

function extractEducation(text: string): any[] {
  const education: any[] = []

  // Look for Education section
  const eduSectionRegex = /education[:\s]+([^]*?)(?=(experience|skills|certifications|$))/i
  const eduMatch = text.match(eduSectionRegex)

  if (!eduMatch) return []

  const eduText = eduMatch[1]
  const entries = eduText.split(/\n\n+/)

  for (const entry of entries.slice(0, 3)) { // Limit to 3 education entries
    if (entry.trim().length < 10) continue

    const lines = entry.split('\n').filter(l => l.trim())
    if (lines.length === 0) continue

    education.push({
      degree: lines[0]?.trim() || 'Degree',
      institution: lines[1]?.trim() || 'Institution',
      graduation_date: 'Date not parsed'
    })
  }

  return education.length > 0 ? education : [{ degree: 'Education not fully parsed', institution: 'See resume' }]
}

function extractSkills(text: string): string[] {
  // Look for Skills section
  const skillsSectionRegex = /skills[:\s]+([^]*?)(?=(experience|education|certifications|$))/i
  const skillsMatch = text.match(skillsSectionRegex)

  if (!skillsMatch) return ['Skills section not found']

  const skillsText = skillsMatch[1]

  // Split by common delimiters
  const skills = skillsText
    .split(/[,•\-\n]/)
    .map(s => s.trim())
    .filter(s => s.length > 2 && s.length < 100)
    .slice(0, 20) // Limit to 20 skills

  return skills.length > 0 ? skills : ['Skills not parsed']
}
