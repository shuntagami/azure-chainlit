import plotly
from typing import Optional, List
from pathlib import Path

import chainlit as cl
from chainlit.context import local_steps
from chainlit.element import Element
from openai import AsyncAssistantEventHandler
from openai.types.beta.threads.runs import RunStep

from literalai.helper import utc_now

from app.services.openai_client import get_openai_client

class EventHandler(AsyncAssistantEventHandler):
    """
    Handles events from OpenAI Assistant runs and updates Chainlit UI accordingly.
    """
    def __init__(self, assistant_name: str) -> None:
        """
        Initialize the event handler.
        
        Args:
            assistant_name: Name of the OpenAI assistant
        """
        super().__init__()
        self.current_message: Optional[cl.Message] = None
        self.current_step: Optional[cl.Step] = None
        self.current_tool_call: Optional[str] = None
        self.assistant_name = assistant_name
        
        # Set up parent step if available
        previous_steps = local_steps.get() or []
        parent_step = previous_steps[-1] if previous_steps else None
        self.parent_id = parent_step.id if parent_step else None

    async def on_run_step_created(self, run_step: RunStep) -> None:
        """Store run step in user session for potential cancellation"""
        cl.user_session.set("run_step", run_step)

    async def on_text_created(self, text) -> None:
        """Initialize a new message when text creation begins"""
        self.current_message = await cl.Message(
            author=self.assistant_name, content=""
        ).send()

    async def on_text_delta(self, delta, snapshot):
        """Stream tokens to the current message"""
        if delta.value:
            await self.current_message.stream_token(delta.value)

    async def on_text_done(self, text):
        """Process completed message text, including handling annotations/files"""
        await self.current_message.update()
        
        # Process any annotations (like file references)
        if text.annotations:
            await self._process_annotations(text.annotations)
    
    async def _process_annotations(self, annotations):
        """Process file annotations, creating appropriate elements"""
        client = get_openai_client()
        
        for annotation in annotations:
            if annotation.type == "file_path":
                try:
                    # Fetch the file content from OpenAI
                    response = await client.files.with_raw_response.content(
                        annotation.file_path.file_id
                    )
                    file_name = annotation.text.split("/")[-1]
                    
                    # Try to process as Plotly JSON first
                    try:
                        fig = plotly.io.from_json(response.content)
                        element = cl.Plotly(name=file_name, figure=fig)
                    except Exception:
                        # Fall back to regular file if not Plotly
                        element = cl.File(content=response.content, name=file_name)
                    
                    # Send the element as a separate message
                    await cl.Message(content="", elements=[element]).send()
                    
                    # Fix links in the message content
                    if (annotation.text in self.current_message.content and element.chainlit_key):
                        self.current_message.content = self.current_message.content.replace(
                            annotation.text,
                            f"/project/file/{element.chainlit_key}?session_id={cl.context.session.id}",
                        )
                        await self.current_message.update()
                except Exception as e:
                    await cl.ErrorMessage(content=f"Error processing annotation: {str(e)}").send()

    async def on_tool_call_created(self, tool_call):
        """Initialize a new step when a tool call begins"""
        self.current_tool_call = tool_call.id
        self.current_step = await self._create_step(tool_call.type)
    
    async def _create_step(self, step_type, tool_call=None):
        """Create and initialize a step with appropriate settings"""
        step = cl.Step(
            name=step_type, 
            type="tool", 
            parent_id=self.parent_id
        )
        
        # Configure step based on type
        if step_type == "code_interpreter":
            step.show_input = "python"
        elif tool_call and tool_call.type == "function":
            step.name = tool_call.function.name if tool_call else step_type
            step.language = "json"
            
        step.start = utc_now()
        await step.send()
        return step

    async def on_tool_call_delta(self, delta, snapshot):
        """Handle updates to tool calls"""
        # Create a new step if tool call ID changed
        if snapshot.id != self.current_tool_call:
            self.current_tool_call = snapshot.id
            self.current_step = await self._create_step(delta.type, snapshot)
        
        # Handle different tool types
        if delta.type == "code_interpreter":
            await self._handle_code_interpreter_delta(delta)
        # Future: Handle other tool types here

    async def _handle_code_interpreter_delta(self, delta):
        """Process code interpreter outputs and inputs"""
        if not self.current_step:
            return
            
        if delta.code_interpreter.outputs:
            for output in delta.code_interpreter.outputs:
                if output.type == "logs":
                    self.current_step.output += output.logs
                    self.current_step.language = "markdown"
                    self.current_step.end = utc_now()
                    await self.current_step.update()
                elif output.type == "image":
                    self.current_step.language = "json"
                    self.current_step.output = output.image.model_dump_json()
        elif delta.code_interpreter.input:
            await self.current_step.stream_token(
                delta.code_interpreter.input, is_input=True
            )

    async def on_event(self, event) -> None:
        """Handle general events from the OpenAI API"""
        if event.event == "error":
            await cl.ErrorMessage(content=str(event.data.message)).send()

    async def on_exception(self, exception: Exception) -> None:
        """Handle exceptions during processing"""
        await cl.ErrorMessage(content=str(exception)).send()

    async def on_tool_call_done(self, tool_call):
        """Finalize the step when a tool call is complete"""
        if self.current_step:
            self.current_step.end = utc_now()
            await self.current_step.update()

    async def on_image_file_done(self, image_file):
        """Process image files generated by the assistant"""
        try:
            client = get_openai_client()
            image_id = image_file.file_id
            response = await client.files.with_raw_response.content(image_id)
            
            # Create and add image element
            image_element = cl.Image(
                name=image_id, 
                content=response.content, 
                display="inline", 
                size="large"
            )
            
            # Initialize elements list if needed
            if not self.current_message.elements:
                self.current_message.elements = []
                
            self.current_message.elements.append(image_element)
            await self.current_message.update()
        except Exception as e:
            await cl.ErrorMessage(content=f"Error processing image: {str(e)}").send()