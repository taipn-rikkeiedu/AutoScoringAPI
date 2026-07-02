import os
import sys
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.ai_service import AIService

def test():
    config_path = "C:/AutoScoring/config/config.json"
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    else:
        print("Config not found!")
        return

    config["provider"] = "gemini"
    
    ai = AIService(config=config)
    assignment = "Viết API Endpoint hoàn chỉnh phục vụ việc chấm điểm mã nguồn."
    # SINGLE CRITERIA!
    criteria = "Cấu hình API Endpoint: 20đ"
    code = "def hello():\n    return 'world'"
    
    full_report = ""
    try:
        for chunk in ai.generate_grading_report_stream(assignment, criteria, code):
            full_report += chunk
            
        with open("scratch/stream_output_single.txt", "w", encoding="utf-8") as f:
            f.write(full_report)
        print("SUCCESS! Output written to scratch/stream_output_single.txt")
    except Exception as e:
        print("ERROR:", e)

if __name__ == "__main__":
    test()
