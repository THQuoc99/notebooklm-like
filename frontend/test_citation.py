"""
Test script for citation rendering
"""
import json

def test_render():
    answer_text = "Thông tin bao gồm giao dịch [1] và công việc [2]."
    sources = [
        {
            "filename": "transaction.pdf",
            "page_start": 1,
            "page_end": 1,
            "title": "Giao dịch chuyển tiền",
            "content": "Ngày: 2026-01-04, Mã: 2054034570, Số tiền: 24,000đ"
        },
        {
            "filename": "work_info.pdf",
            "page_start": 2,
            "page_end": 2,
            "title": "Thông tin công việc",
            "content": "Địa chỉ: 381 Tran Hung Dao, Ngày bắt đầu: 05/01/2026"
        }
    ]
    
    sources_json = json.dumps(sources, ensure_ascii=False)
    answer_json = json.dumps(answer_text)
    
    print("Answer text:", answer_json)
    print("\nSources JSON:", sources_json)
    print("\nPattern test:")
    
    import re
    pattern = r'\[(\d+)\]'
    matches = re.findall(pattern, answer_text)
    print(f"Found citations: {matches}")
    
    # Test JavaScript regex pattern
    js_pattern = r'\[(\d+)\]'
    for match in re.finditer(js_pattern, answer_text):
        print(f"Match: {match.group(0)} at position {match.start()}-{match.end()}")
        print(f"  Number: {match.group(1)}")

if __name__ == "__main__":
    test_render()
