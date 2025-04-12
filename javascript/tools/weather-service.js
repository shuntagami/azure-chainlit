// A mock weather service tool for MCP
const weatherService = {
  description: 'Get weather information for a location',
  inputSchema: {
    type: 'object',
    properties: {
      location: {
        type: 'string',
        description: 'The location to get weather for (city name)',
      },
    },
    required: ['location'],
  },

  // Mock weather data
  weatherData: {
    'Tokyo': { temp: 25, condition: 'Sunny', humidity: 60 },
    'New York': { temp: 18, condition: 'Cloudy', humidity: 70 },
    'London': { temp: 15, condition: 'Rainy', humidity: 80 },
    'Sydney': { temp: 28, condition: 'Sunny', humidity: 50 },
    'Paris': { temp: 20, condition: 'Partly Cloudy', humidity: 65 },
  },

  // Execute the weather service
  async execute(input) {
    const { location } = input;

    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 500));

    const weatherInfo = this.weatherData[location];

    if (!weatherInfo) {
      return {
        error: 'Location not found',
        available_locations: Object.keys(this.weatherData)
      };
    }

    return {
      location,
      temperature: weatherInfo.temp,
      condition: weatherInfo.condition,
      humidity: weatherInfo.humidity,
      unit: 'celsius',
      time: new Date().toISOString()
    };
  },
};

module.exports = weatherService;
