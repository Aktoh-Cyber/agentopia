#!/usr/bin/env node
/**
 * Test script for LangGraph agent generation
 * Tests both JavaScript and Python builders with LangGraph patterns
 */

import { buildAgentFromFile } from './generators/javascript/agent-builder.js';
import { spawn } from 'child_process';
import { promises as fs } from 'fs';
import path from 'path';

const testOutputDir = './test-langgraph-output';

async function testJavaScriptBuilder() {
  console.log('🟡 Testing JavaScript LangGraph Agent Builder...');
  
  try {
    // Test supervisor pattern
    const configPath = './generators/javascript/configs/supervisor-example.json';
    const outputDir = path.join(testOutputDir, 'js-supervisor-test');
    
    await buildAgentFromFile(configPath, outputDir);
    console.log('✅ JavaScript supervisor agent generated successfully');
    
    // Verify key files exist
    const expectedFiles = [
      'src/index.js',
      'package.json',
      'wrangler.toml',
      'scripts/deploy-all.sh',
      'README.md'
    ];
    
    for (const file of expectedFiles) {
      const filePath = path.join(outputDir, file);
      try {
        await fs.access(filePath);
        console.log(`✅ Generated ${file}`);
      } catch (error) {
        console.log(`❌ Missing ${file}`);
      }
    }
    
    // Check if the generated index.js imports LangGraphAgent
    const indexContent = await fs.readFile(path.join(outputDir, 'src/index.js'), 'utf-8');
    if (indexContent.includes('LangGraphAgent')) {
      console.log('✅ LangGraphAgent import found in generated code');
    } else {
      console.log('❌ LangGraphAgent import not found');
    }
    
  } catch (error) {
    console.error('❌ JavaScript builder test failed:', error.message);
  }
}

async function testPythonBuilder() {
  console.log('\n🟡 Testing Python LangGraph Agent Builder...');
  
  try {
    // Test committee pattern
    const configPath = './generators/python/configs/pipeline-example.json';
    const outputDir = path.join(testOutputDir, 'py-pipeline-test');
    
    const pythonProcess = spawn('python3', [
      './generators/python/agent_builder.py',
      configPath,
      outputDir
    ], { stdio: 'pipe' });
    
    let output = '';
    pythonProcess.stdout.on('data', (data) => {
      output += data.toString();
    });
    
    pythonProcess.stderr.on('data', (data) => {
      console.error('Python stderr:', data.toString());
    });
    
    await new Promise((resolve, reject) => {
      pythonProcess.on('close', (code) => {
        if (code === 0) {
          console.log('✅ Python pipeline agent generated successfully');
          console.log(output);
          resolve();
        } else {
          reject(new Error(`Python process exited with code ${code}`));
        }
      });
    });
    
    // Verify key files exist
    const expectedFiles = [
      'src/entry.py',
      'wrangler.toml',
      'scripts/deploy.sh',  
      'README.md'
    ];
    
    for (const file of expectedFiles) {
      const filePath = path.join(outputDir, file);
      try {
        await fs.access(filePath);
        console.log(`✅ Generated ${file}`);
      } catch (error) {
        console.log(`❌ Missing ${file}`);
      }
    }
    
    // Check if the generated entry.py imports LangGraphAgent
    const entryContent = await fs.readFile(path.join(outputDir, 'src/entry.py'), 'utf-8');
    if (entryContent.includes('LangGraphAgent')) {
      console.log('✅ LangGraphAgent import found in generated code');
    } else {
      console.log('❌ LangGraphAgent import not found');
    }
    
  } catch (error) {
    console.error('❌ Python builder test failed:', error.message);
  }
}

async function main() {
  console.log('🚀 Testing LangGraph Agent Builders\n');
  
  // Clean test output directory
  try {
    await fs.rm(testOutputDir, { recursive: true, force: true });
  } catch (error) {
    // Directory might not exist
  }
  
  await fs.mkdir(testOutputDir, { recursive: true });
  
  await testJavaScriptBuilder();
  await testPythonBuilder();
  
  console.log('\n🎉 LangGraph agent builder tests completed!');
  console.log(`📁 Test outputs available in: ${testOutputDir}`);
}

main().catch(console.error);