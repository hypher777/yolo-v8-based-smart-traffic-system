class EmergencyHandler:
    def __init__(self):
        self.priority_map = {
            'ambulance': 1,
            'fire truck': 2
        }

    def check_emergency(self, emergency_list):
        """
        Check if any emergency vehicle is present and determine the highest priority.
        Returns:
            - is_emergency (bool): True if any emergency vehicle detected
            - priority_type (str): The type of the highest priority vehicle found (or None)
        """
        if not emergency_list:
            return False, None
            
        # Find highest priority (lowest number in checking order, actually 1 is highest)
        best_priority = 999
        best_type = None
        
        for ev in emergency_list:
            p = self.priority_map.get(ev, 999)
            if p < best_priority:
                best_priority = p
                best_type = ev
                
        return True, best_type
