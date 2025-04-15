const calculator = require('./calculator');
const weatherService = require('./weather-service');

// Registry of available tools
const toolRegistry = {
  calculator: calculator,
  weather: weatherService,
  // Add more tools here
};

// Get metadata for all available tools
function getToolMetadata() {
  return Object.entries(toolRegistry).map(([name, tool]) => ({
    name,
    description: tool.description,
    inputSchema: tool.inputSchema,
  }));
}

// Call a specific tool with input
async function callTool(toolName, input) {
  const tool = toolRegistry[toolName];

  if (!tool) {
    throw new Error(`Tool "${toolName}" not found`);
  }

  return await tool.execute(input);
}

module.exports = {
  getToolMetadata,
  callTool,
};
