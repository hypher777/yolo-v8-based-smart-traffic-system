import time

class TrafficController:
    def __init__(self, num_roads=4, min_green_time=5, max_green_time=30, max_wait_time=25, yellow_time=2):
        self.num_roads = num_roads
        self.min_green_time = min_green_time
        self.max_green_time = max_green_time
        self.max_wait_time = max_wait_time
        self.yellow_time = yellow_time
        self.emergency_yellow_time = 1.0 # Faster transition for emergency safety
        
        # State
        self.current_green = 0  # Road index 0-3
        self.next_green = -1    # Road index to switch to after yellow
        self.last_switch_time = time.time()
        self.yellow_start_time = 0
        self.is_emergency_mode = False
        
        # Track when each road last became RED (to compute wait time)
        self.red_start_times = [time.time()] * num_roads
        
        # Initial State: Road 0 is Green
        self.states = ["RED"] * num_roads
        self.states[0] = "GREEN"

    def decide_signals(self, vehicle_counts, emergency_status):
        current_time = time.time()
        time_elapsed = current_time - self.last_switch_time
        
        # 0. HANDLE YELLOW TRANSITION
        if self.next_green != -1:
            # Use standard or quick yellow depending on mode
            y_time = self.emergency_yellow_time if self.is_emergency_mode else self.yellow_time
            if current_time - self.yellow_start_time >= y_time:
                # Transition complete: Yellow -> Red, Next -> Green
                old_green = self.current_green
                self.current_green = self.next_green
                self.next_green = -1
                
                self.states = ["RED"] * self.num_roads
                self.states[self.current_green] = "GREEN"
                self.last_switch_time = current_time
                self.red_start_times[old_green] = current_time
                
                print(f"--- [TRANSITION] Road {self.current_green+1} is now GREEN ---")
                return self.states, True
            return self.states, False

        # 1. EMERGENCY OVERRIDE
        emergency_road = -1
        for i, status in enumerate(emergency_status):
            if status: 
                emergency_road = i
                break 
        
        if emergency_road != -1:
            if self.current_green != emergency_road:
                print(f"\n--- [EMERGENCY] Initiating INSTANT switch to Road {emergency_road+1} ---")
                self.is_emergency_mode = True # Set mode for quick yellow
                self._init_switch(emergency_road)
                return self.states, True
            self.is_emergency_mode = True # Stay in mode if already green
            return self.states, False
        
        self.is_emergency_mode = False

        # Pre-calculation
        roads_with_cars = [i for i, count in enumerate(vehicle_counts) if count > 0]
        
        # 2. EXCLUSIVE ROAD AVAILABILITY / HARD RULE
        if 0 in roads_with_cars and len(roads_with_cars) == 1:
            if self.current_green != 0:
                print("\n--- [HARD RULE] Road-1 priority switch ---")
                self._init_switch(0)
                return self.states, True
            return self.states, False

        if len(roads_with_cars) == 1:
            only_road = roads_with_cars[0]
            if self.current_green != only_road:
                print(f"\n--- [EXCLUSIVE] Only Road {only_road+1} has cars. ---")
                self._init_switch(only_road)
                return self.states, True
            return self.states, False

        # 3. MINIMUM GREEN TIME CHECK
        # (Allows density/fairness to take over only after min_green_time)
        if time_elapsed < self.min_green_time:
            return self.states, False

        # 4. FAIRNESS / STARVATION
        starving_road = -1
        for i in range(self.num_roads):
            if i == self.current_green: continue
            if vehicle_counts[i] > 0:
                wait_duration = current_time - self.red_start_times[i]
                if wait_duration > self.max_wait_time:
                    starving_road = i
                    break

        if starving_road != -1:
            print(f"\n--- [FAIRNESS] Wait limit hit for Road {starving_road+1} ---")
            self._init_switch(starving_road)
            return self.states, True

        # 5. DENSITY
        max_count = max(vehicle_counts) if vehicle_counts else 0
        
        if max_count > 0:
            candidates = [i for i, c in enumerate(vehicle_counts) if c == max_count]
            
            # Change if current road is empty OR if another road has significantly more traffic
            # OR if we hit max_green_time
            if self.current_green not in candidates or time_elapsed >= self.max_green_time:
                max_road = candidates[0]
                if max_road != self.current_green:
                    print(f"\n--- [DENSITY/MAX GREEN] Switching to Road {max_road+1} ---")
                    self._init_switch(max_road)
                    return self.states, True

        return self.states, False

    def _init_switch(self, new_green_index):
        """Starts the yellow transition phase."""
        self.next_green = new_green_index
        self.yellow_start_time = time.time()
        
        # Set current green to YELLOW
        self.states[self.current_green] = "YELLOW"
        # Others stay RED
