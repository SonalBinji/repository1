from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from tools import WeatherMCPTool


class TravelAgent:
    def __init__(self, groq_api_key: str, weather_api_key: str):
        self.llm = ChatGroq(api_key=groq_api_key, model="llama3-70b-8192", temperature=0.3)

        self.weather_tool = WeatherMCPTool(api_key=weather_api_key)
        self.tools = [self.weather_tool]

        # Create the agent
        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are an expert travel assistant with access to real-time weather data. 
            Your role is to provide comprehensive travel suggestions based on weather conditions.
            
            When providing travel suggestions, consider:
            1. Current weather conditions and forecasts
            2. Seasonal activities suitable for the weather
            3. What to pack based on weather conditions
            4. Indoor/outdoor activity recommendations
            5. Best times to visit during the day
            6. Weather-related travel tips and precautions
            
            Always use the weather tool to get current conditions before making suggestions.
            Be specific, practical, and considerate of weather impacts on travel plans.
            Format your responses in a clear, organized manner with specific recommendations.""",
                ),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        self.agent = create_tool_calling_agent(self.llm, self.tools, self.prompt)
        self.agent_executor = AgentExecutor(
            agent=self.agent, tools=self.tools, verbose=True, handle_parsing_errors=True
        )

    def get_travel_suggestions(self, location: str, travel_type: str = "general") -> str:
        query = f"""
        I'm planning to visit {location}. Please get the current weather and forecast, 
        then provide detailed travel suggestions for a {travel_type} trip.
        
        Include:
        - Current weather analysis
        - What to pack recommendations
        - Activity suggestions (both indoor and outdoor)
        - Best times to visit during the day
        - Any weather-related precautions
        - Local seasonal highlights
        """

        try:
            result = self.agent_executor.invoke({"input": query})
            return result["output"]
        except Exception as e:
            return f"Error generating travel suggestions: {str(e)}"