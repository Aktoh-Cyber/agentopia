#!/usr/bin/env node

/**
 * Build Agent CLI Tool
 * Usage: node build-agent.js <config-file> <output-directory>
 */

import { buildAgentFromFile } from './agent-builder.js';
import { readFileSync } from 'fs';
import { resolve } from 'path';

async function main() {
  const args = process.argv.slice(2);
  
  if (args.length < 2) {
    console.error('Usage: node build-agent.js <config-file> <output-directory>');
    console.error('');
    console.error('Examples:');
    console.error('  node build-agent.js configs/judge-specialist.json ../judge-generated');
    console.error('  node build-agent.js configs/threat-intel-specialist.json ../threat-intel');
    process.exit(1);
  }

  const configPath = resolve(args[0]);
  const outputDir = resolve(args[1]);

  try {
    console.log(`🔧 Building agent from ${configPath}`);
    console.log(`📁 Output directory: ${outputDir}`);
    console.log('');

    // Validate config file exists
    try {
      readFileSync(configPath, 'utf-8');
    } catch (error) {
      console.error(`❌ Config file not found: ${configPath}`);
      process.exit(1);
    }

    // Build the agent
    const files = await buildAgentFromFile(configPath, outputDir);
    
    console.log('✅ Agent generated successfully!');
    console.log('');
    console.log('📋 Generated files:');
    Object.keys(files).forEach(file => {
      console.log(`   ${file}`);
    });
    
    console.log('');
    console.log('🚀 Next steps:');
    console.log(`   1. cd ${outputDir}`);
    console.log('   2. Set your Cloudflare API token: export CLOUDFLARE_API_TOKEN="your-token"');
    console.log('   3. Deploy: ./scripts/deploy-all.sh');
    
  } catch (error) {
    console.error('❌ Error building agent:', error.message);
    process.exit(1);
  }
}

main().catch(console.error);