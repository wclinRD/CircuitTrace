from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os

class WaveformParser:
    _instance = None

    def __init__(self):
        self.vcd_file = None
        self.vcd_obj = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = WaveformParser()
        return cls._instance

    def load_vcd(self, file_path: str):
        if self.vcd_file == file_path and self.vcd_obj is not None:
            return True # Already loaded
            
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"VCD file not found: {file_path}")
            
        try:
            from vcdvcd import VCDVCD
            self.vcd_obj = VCDVCD(file_path)
            self.vcd_file = file_path
            return True
        except Exception as e:
            self.vcd_file = None
            self.vcd_obj = None
            raise e

    def get_hierarchy(self) -> Dict[str, Any]:
        if not self.vcd_obj:
            return {"error": "No VCD loaded"}
            
        signals = self.vcd_obj.get_signals()
        
        # Build tree
        tree = {}
        for sig in signals:
            parts = sig.split('.')
            curr = tree
            for i, part in enumerate(parts):
                if i == len(parts) - 1:
                    # Leaf
                    if part not in curr:
                        curr[part] = {"type": "signal", "full_name": sig}
                else:
                    if part not in curr:
                        curr[part] = {"type": "module", "children": {}}
                    curr = curr[part]["children"]
                    
        return tree

    def get_signal_data(self, signal_name: str, start_time: int, end_time: int) -> List[tuple]:
        if not self.vcd_obj:
            return []
            
        if signal_name not in self.vcd_obj.signals:
            return []
            
        tv = self.vcd_obj[signal_name].tv
        # tv is a list of (time, value)
        # We need to find the data points in [start_time, end_time]
        # And also include the last value BEFORE start_time to draw correctly
        
        result = []
        last_val_before_start = None
        
        for t, v in tv:
            if t < start_time:
                last_val_before_start = (t, v)
            elif start_time <= t <= end_time:
                result.append((t, v))
            elif t > end_time:
                # Add the first one after end_time to complete the drawing
                result.append((t, v))
                break
                
        if last_val_before_start and (not result or result[0][0] > start_time):
            # Prepend the value that was held at start_time
            result.insert(0, last_val_before_start)
            
        return result
