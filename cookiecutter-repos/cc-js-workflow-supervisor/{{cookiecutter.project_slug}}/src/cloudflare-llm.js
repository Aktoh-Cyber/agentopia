/**
 * Cloudflare Workers LLM for LangChain
 * Custom LLM implementation for Cloudflare Workers AI
 */

import { LLM } from "@langchain/core/language_models/llms";
import { Ai } from '@cloudflare/ai';

export class CloudflareWorkersLLM extends LLM {
  constructor(fields = {}) {
    super(fields);
    this.model = fields.model || '@cf/meta/llama-3.1-70b-instruct';
    this.maxTokens = fields.maxTokens || 1000;
    this.temperature = fields.temperature || 0.7;
    this.env = fields.env;
  }
  
  _llmType() {
    return "cloudflare-workers";
  }
  
  async _call(prompt, options) {
    if (!this.env || !this.env.AI) {
      throw new Error("Cloudflare AI binding not available. Make sure env.AI is provided.");
    }
    
    const ai = new Ai(this.env.AI);
    
    const response = await ai.run(this.model, {
      prompt,
      max_tokens: this.maxTokens,
      temperature: this.temperature,
      ...options
    });
    
    if (response.response) {
      return response.response;
    }
    
    // Handle chat models that expect messages
    const messagesResponse = await ai.run(this.model, {
      messages: [{ role: 'user', content: prompt }],
      max_tokens: this.maxTokens,
      temperature: this.temperature,
      ...options
    });
    
    return messagesResponse.response || "";
  }
  
  async _generate(prompts, options) {
    const generations = await Promise.all(
      prompts.map(async (prompt) => {
        const text = await this._call(prompt, options);
        return [{ text }];
      })
    );
    return { generations };
  }
}