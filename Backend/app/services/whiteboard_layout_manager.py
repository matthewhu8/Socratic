"""
Whiteboard Layout Manager
Manages whiteboard space to avoid overlapping and optimize visual organization
"""

from typing import Dict, List, Optional, Any
import json

class WhiteboardLayoutManager:
    """Manages whiteboard space to avoid overlapping"""
    
    def __init__(self, canvas_width: int = 800, canvas_height: int = 2000):
        self.width = canvas_width
        self.height = canvas_height
        self.occupied_regions = []
        self.student_regions = []
        
    async def analyze_student_work(self, canvas_image: str, gemini_service) -> Dict:
        """Detect where student has drawn using image analysis"""
        analysis_prompt = """
Analyze this whiteboard image and identify:
1. Regions where student has written/drawn (return bounding boxes)
2. Type of content in each region (equation, diagram, text, etc.)
3. Any specific annotations or marks that seem like questions

Output JSON:
{
    "student_regions": [
        {"x": 0, "y": 0, "width": 100, "height": 50, "content": "equation: x+2=5"},
        {"x": 150, "y": 100, "width": 80, "height": 80, "content": "question_mark"}
    ],
    "empty_zones": [
        {"x": 0, "y": 200, "width": 400, "height": 300}
    ]
}
"""
        
        result = await gemini_service.generate_simple_response(analysis_prompt, canvas_image)
        self.student_regions = result.get("student_regions", [])
        return result
    
    def find_optimal_zone(self, required_size: Dict, near_location: Optional[Dict] = None) -> Dict:
        """Find best location for new drawing"""
        # Simple implementation - find first available space
        start_y = 50
        if near_location:
            start_y = near_location.get("y", 50) + near_location.get("height", 0) + 20
        
        # Check for conflicts with student regions
        while self._has_conflict({"x": 50, "y": start_y, **required_size}):
            start_y += 50
        
        return {
            "x": 50,
            "y": start_y,
            "width": required_size.get("width", 400),
            "height": required_size.get("height", 200)
        }
    
    def _has_conflict(self, proposed_zone: Dict) -> bool:
        """Check if proposed zone conflicts with existing content"""
        for region in self.student_regions:
            if self._zones_overlap(proposed_zone, region):
                return True
        return False
    
    def _zones_overlap(self, zone1: Dict, zone2: Dict) -> bool:
        """Check if two zones overlap"""
        return not (
            zone1["x"] + zone1["width"] < zone2["x"] or
            zone2["x"] + zone2["width"] < zone1["x"] or
            zone1["y"] + zone1["height"] < zone2["y"] or
            zone2["y"] + zone2["height"] < zone1["y"]
        )