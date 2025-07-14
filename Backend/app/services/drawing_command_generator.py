"""
Specialized Drawing Command Generators
"""

from typing import Dict, List, Optional, Any
import json

class DrawingCommandGenerator:
    """Base class for specialized drawing command generators"""
    
    def __init__(self, gemini_service):
        self.gemini_service = gemini_service
    
    async def generate_equation_steps(self, equation: str, zone: Dict) -> List[Dict]:
        """Generate step-by-step equation solving visuals"""
        prompt = f"""
Draw equation solving steps for: {equation}
Start at x={zone['x']}, y={zone['y']}

Style guide:
- Original equation in black
- Operations in blue (e.g., "+5 to both sides")
- Results in green
- 40px spacing between steps

Output only drawing commands JSON array.
"""
        return await self.gemini_service.generate_drawing_commands_only(prompt)
    
    async def generate_graph(self, function: str, zone: Dict) -> List[Dict]:
        """Generate coordinate plane and function graph"""
        prompt = f"""
Draw a coordinate plane with function: {function}
Center at x={zone['x'] + zone['width']//2}, y={zone['y'] + zone['height']//2}

Include:
- Axes with labels
- Grid lines (dashed, light gray)
- Function curve in blue
- Key points marked

Output only drawing commands JSON array.
"""
        return await self.gemini_service.generate_drawing_commands_only(prompt)
    
    async def generate_geometry_diagram(self, shape_desc: str, zone: Dict) -> List[Dict]:
        """Generate geometric diagrams with annotations"""
        prompt = f"""
Draw geometric diagram: {shape_desc}
In zone: x={zone['x']}, y={zone['y']}, width={zone['width']}, height={zone['height']}

Include:
- Clear shape outlines
- Labeled angles and sides
- Measurements if provided
- Color coding for different elements

Output only drawing commands JSON array.
"""
        return await self.gemini_service.generate_drawing_commands_only(prompt)
    
    async def generate_correction_overlay(self, error_location: Dict, correction: str) -> List[Dict]:
        """Generate correction marks over student work"""
        prompt = f"""
Draw correction at x={error_location['x']}, y={error_location['y']}:
- Red circle around error
- Correction in green nearby
- Arrow pointing from error to correction

Correction text: {correction}

Output only drawing commands JSON array.
"""
        return await self.gemini_service.generate_drawing_commands_only(prompt)