#!/usr/bin/env node
import { readFile } from 'node:fs/promises'
import { resolve } from 'node:path'

const path = resolve(process.argv[2] ?? 'demo-blueprint.yaml')
const text = await readFile(path, 'utf8')
const errors: string[] = []
const warnings: string[] = []
const required = ['source:', 'intent:', 'architecture:', 'operational_pattern:', 'evidence:', 'decisions:', 'ai_assessment:', 'story_mapping:']
for (const section of required) if (!text.includes(`\n${section}`) && !text.startsWith(section)) errors.push(`Missing required section: ${section.slice(0, -1)}`)
if (!/operational_pattern:[\s\S]*?steps:\s*\n\s+-\s+/m.test(text)) errors.push('Operational pattern needs at least one domain-specific step.')
if (!/architecture:[\s\S]*?flows:\s*\n\s+-\s+/m.test(text)) errors.push('Architecture needs at least one typed end-to-end flow.')
if (!/evidence:\s*\n\s+-\s+/m.test(text)) errors.push('Blueprint needs at least one evidence item.')
if (/needed:\s*(true|optional)/.test(text)) {
  for (const field of ['rationale:', 'tasks:', 'inputs:', 'outputs:', 'action_authority:', 'fallback:', 'final_decision_owner:']) {
    if (!new RegExp(`ai_assessment:[\\s\\S]*?${field.replace(':', '\\:')}`).test(text)) errors.push(`AI assessment is missing ${field.slice(0, -1)}.`)
  }
  if (/action_authority:\s*(unknown|null)/.test(text)) errors.push('AI action authority must be resolved before release.')
  if (/final_decision_owner:\s*(unknown|null)/.test(text)) errors.push('AI final decision owner must be resolved before release.')
}
const unknowns = (text.match(/:\s*unknown\s*$/gm) ?? []).length
if (unknowns) warnings.push(`${unknowns} unresolved field(s) remain.`)
if (!/status:\s*(reviewed|approved)/.test(text)) warnings.push('Blueprint is still draft; material claims require review.')

for (const warning of warnings) console.warn(`WARN ${warning}`)
for (const error of errors) console.error(`ERROR ${error}`)
if (errors.length) process.exit(1)
console.log(`Blueprint structure is valid: ${path}`)
