#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Journal App
Tests all CRUD operations, AI mood analysis, and trend calculations
"""

import requests
import json
import time
from datetime import datetime, date, timedelta
import uuid

# Configuration
BASE_URL = "https://moodtracker-journal.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class JournalAPITester:
    def __init__(self):
        self.base_url = BASE_URL
        self.headers = HEADERS
        self.test_entries = []
        self.test_results = {
            "crud_operations": {"passed": 0, "failed": 0, "details": []},
            "ai_analysis": {"passed": 0, "failed": 0, "details": []},
            "mood_trends": {"passed": 0, "failed": 0, "details": []},
            "tags_management": {"passed": 0, "failed": 0, "details": []}
        }
    
    def log_result(self, category, test_name, passed, details=""):
        """Log test result"""
        if passed:
            self.test_results[category]["passed"] += 1
            status = "✅ PASS"
        else:
            self.test_results[category]["failed"] += 1
            status = "❌ FAIL"
        
        self.test_results[category]["details"].append(f"{status}: {test_name} - {details}")
        print(f"{status}: {test_name} - {details}")
    
    def test_api_health(self):
        """Test if API is accessible"""
        print("\n=== Testing API Health ===")
        try:
            response = requests.get(f"{self.base_url}/", timeout=10)
            if response.status_code == 200:
                print("✅ API is accessible")
                return True
            else:
                print(f"❌ API returned status code: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ API connection failed: {e}")
            return False
    
    def test_create_entry(self, title, content, tags=None, expected_emotions=None):
        """Test creating a journal entry with AI analysis"""
        if tags is None:
            tags = []
        
        entry_data = {
            "title": title,
            "content": content,
            "tags": tags
        }
        
        try:
            response = requests.post(f"{self.base_url}/entries", 
                                   json=entry_data, 
                                   headers=self.headers,
                                   timeout=30)
            
            if response.status_code == 200:
                entry = response.json()
                
                # Validate response structure
                required_fields = ["id", "title", "content", "mood_score", "mood_emotion", "ai_summary", "date", "created_at"]
                missing_fields = [field for field in required_fields if field not in entry]
                
                if missing_fields:
                    self.log_result("crud_operations", f"Create Entry '{title}'", False, 
                                  f"Missing fields: {missing_fields}")
                    return None
                
                # Validate AI analysis
                mood_score = entry.get("mood_score")
                mood_emotion = entry.get("mood_emotion")
                ai_summary = entry.get("ai_summary")
                
                ai_valid = True
                ai_details = []
                
                if not isinstance(mood_score, int) or not (1 <= mood_score <= 10):
                    ai_valid = False
                    ai_details.append(f"Invalid mood_score: {mood_score}")
                
                if not mood_emotion or mood_emotion == "Analysis temporarily unavailable":
                    ai_valid = False
                    ai_details.append(f"Invalid mood_emotion: {mood_emotion}")
                
                if not ai_summary or ai_summary == "Analysis temporarily unavailable":
                    ai_valid = False
                    ai_details.append(f"Invalid ai_summary: {ai_summary}")
                
                # Log results
                self.log_result("crud_operations", f"Create Entry '{title}'", True, 
                              f"Entry created with ID: {entry['id']}")
                
                if ai_valid:
                    self.log_result("ai_analysis", f"AI Analysis for '{title}'", True,
                                  f"Score: {mood_score}, Emotion: {mood_emotion}")
                else:
                    self.log_result("ai_analysis", f"AI Analysis for '{title}'", False,
                                  f"Issues: {'; '.join(ai_details)}")
                
                # Check expected emotions if provided
                if expected_emotions and mood_emotion not in expected_emotions:
                    self.log_result("ai_analysis", f"Expected Emotion for '{title}'", False,
                                  f"Got '{mood_emotion}', expected one of {expected_emotions}")
                
                self.test_entries.append(entry)
                return entry
            else:
                self.log_result("crud_operations", f"Create Entry '{title}'", False,
                              f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_result("crud_operations", f"Create Entry '{title}'", False, str(e))
            return None
    
    def test_get_entries(self):
        """Test fetching all entries"""
        try:
            response = requests.get(f"{self.base_url}/entries", timeout=10)
            
            if response.status_code == 200:
                entries = response.json()
                if isinstance(entries, list):
                    self.log_result("crud_operations", "Get All Entries", True,
                                  f"Retrieved {len(entries)} entries")
                    return entries
                else:
                    self.log_result("crud_operations", "Get All Entries", False,
                                  "Response is not a list")
                    return None
            else:
                self.log_result("crud_operations", "Get All Entries", False,
                              f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_result("crud_operations", "Get All Entries", False, str(e))
            return None
    
    def test_get_entry_by_id(self, entry_id):
        """Test fetching a specific entry"""
        try:
            response = requests.get(f"{self.base_url}/entries/{entry_id}", timeout=10)
            
            if response.status_code == 200:
                entry = response.json()
                if entry.get("id") == entry_id:
                    self.log_result("crud_operations", f"Get Entry by ID", True,
                                  f"Retrieved entry: {entry['title']}")
                    return entry
                else:
                    self.log_result("crud_operations", f"Get Entry by ID", False,
                                  "ID mismatch in response")
                    return None
            elif response.status_code == 404:
                self.log_result("crud_operations", f"Get Entry by ID", True,
                              "Correctly returned 404 for non-existent entry")
                return None
            else:
                self.log_result("crud_operations", f"Get Entry by ID", False,
                              f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_result("crud_operations", f"Get Entry by ID", False, str(e))
            return None
    
    def test_update_entry(self, entry_id, new_title, new_content, new_tags=None):
        """Test updating an entry"""
        if new_tags is None:
            new_tags = []
        
        update_data = {
            "title": new_title,
            "content": new_content,
            "tags": new_tags
        }
        
        try:
            response = requests.put(f"{self.base_url}/entries/{entry_id}",
                                  json=update_data,
                                  headers=self.headers,
                                  timeout=30)
            
            if response.status_code == 200:
                updated_entry = response.json()
                
                # Verify update
                if (updated_entry.get("title") == new_title and 
                    updated_entry.get("content") == new_content):
                    
                    self.log_result("crud_operations", "Update Entry", True,
                                  f"Entry updated successfully")
                    
                    # Check if AI re-analysis happened
                    if updated_entry.get("mood_score") and updated_entry.get("mood_emotion"):
                        self.log_result("ai_analysis", "Re-analysis on Update", True,
                                      f"New mood: {updated_entry['mood_emotion']}")
                    else:
                        self.log_result("ai_analysis", "Re-analysis on Update", False,
                                      "AI analysis not performed on update")
                    
                    return updated_entry
                else:
                    self.log_result("crud_operations", "Update Entry", False,
                                  "Update data not reflected in response")
                    return None
            else:
                self.log_result("crud_operations", "Update Entry", False,
                              f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_result("crud_operations", "Update Entry", False, str(e))
            return None
    
    def test_delete_entry(self, entry_id):
        """Test deleting an entry"""
        try:
            response = requests.delete(f"{self.base_url}/entries/{entry_id}", timeout=10)
            
            if response.status_code == 200:
                self.log_result("crud_operations", "Delete Entry", True,
                              "Entry deleted successfully")
                return True
            elif response.status_code == 404:
                self.log_result("crud_operations", "Delete Entry", True,
                              "Correctly returned 404 for non-existent entry")
                return True
            else:
                self.log_result("crud_operations", "Delete Entry", False,
                              f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("crud_operations", "Delete Entry", False, str(e))
            return False
    
    def test_weekly_mood_trends(self):
        """Test weekly mood trends API"""
        try:
            response = requests.get(f"{self.base_url}/mood-trends/weekly", timeout=10)
            
            if response.status_code == 200:
                trends = response.json()
                
                # Validate structure
                required_fields = ["weekly_trends", "average_mood", "most_common_emotion", "total_entries"]
                missing_fields = [field for field in required_fields if field not in trends]
                
                if missing_fields:
                    self.log_result("mood_trends", "Weekly Trends Structure", False,
                                  f"Missing fields: {missing_fields}")
                    return None
                
                # Validate data types
                if not isinstance(trends["weekly_trends"], list):
                    self.log_result("mood_trends", "Weekly Trends Data", False,
                                  "weekly_trends is not a list")
                    return None
                
                if not isinstance(trends["average_mood"], (int, float)):
                    self.log_result("mood_trends", "Average Mood Type", False,
                                  f"average_mood is not numeric: {type(trends['average_mood'])}")
                    return None
                
                if not isinstance(trends["total_entries"], int):
                    self.log_result("mood_trends", "Total Entries Type", False,
                                  f"total_entries is not int: {type(trends['total_entries'])}")
                    return None
                
                self.log_result("mood_trends", "Weekly Trends API", True,
                              f"Retrieved trends for {trends['total_entries']} entries, avg mood: {trends['average_mood']}")
                
                # Validate trend data structure
                for i, trend in enumerate(trends["weekly_trends"]):
                    if not all(key in trend for key in ["date", "mood_score", "mood_emotion"]):
                        self.log_result("mood_trends", f"Trend Item {i}", False,
                                      "Missing required fields in trend item")
                    else:
                        self.log_result("mood_trends", f"Trend Item {i}", True,
                                      f"Valid trend: {trend['date']} - {trend['mood_emotion']}")
                
                return trends
            else:
                self.log_result("mood_trends", "Weekly Trends API", False,
                              f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_result("mood_trends", "Weekly Trends API", False, str(e))
            return None
    
    def test_tags_management(self):
        """Test tags management API"""
        try:
            response = requests.get(f"{self.base_url}/tags", timeout=10)
            
            if response.status_code == 200:
                tags_response = response.json()
                
                if "tags" in tags_response and isinstance(tags_response["tags"], list):
                    tags = tags_response["tags"]
                    self.log_result("tags_management", "Get All Tags", True,
                                  f"Retrieved {len(tags)} unique tags: {tags}")
                    return tags
                else:
                    self.log_result("tags_management", "Get All Tags", False,
                                  "Invalid response structure")
                    return None
            else:
                self.log_result("tags_management", "Get All Tags", False,
                              f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_result("tags_management", "Get All Tags", False, str(e))
            return None
    
    def run_comprehensive_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting Comprehensive Journal App Backend Testing")
        print("=" * 60)
        
        # Test API health first
        if not self.test_api_health():
            print("❌ API is not accessible. Stopping tests.")
            return
        
        print("\n=== Testing Journal Entry CRUD Operations ===")
        
        # Test creating entries with different emotional content
        test_entries_data = [
            {
                "title": "Amazing Day at the Beach",
                "content": "Today was absolutely wonderful! I spent the entire day at the beach with my family. The sun was shining, the waves were perfect, and we had such a great time building sandcastles and swimming. I feel so grateful and happy right now. Life is beautiful!",
                "tags": ["family", "beach", "vacation"],
                "expected_emotions": ["happy", "grateful", "excited", "content"]
            },
            {
                "title": "Struggling with Work Stress",
                "content": "Work has been really overwhelming lately. I have so many deadlines and my boss keeps piling on more tasks. I barely have time to breathe and I'm feeling really anxious about everything. I don't know how I'm going to manage all of this.",
                "tags": ["work", "stress"],
                "expected_emotions": ["anxious", "stressed", "sad"]
            },
            {
                "title": "Peaceful Morning Meditation",
                "content": "I started my day with a 20-minute meditation session in my garden. The birds were chirping softly and there was a gentle breeze. I feel so centered and calm now. It's amazing how a few minutes of mindfulness can completely change my perspective.",
                "tags": ["meditation", "mindfulness", "morning"],
                "expected_emotions": ["calm", "content", "grateful"]
            },
            {
                "title": "Exciting Job Interview",
                "content": "I just finished my interview for the dream job I've been wanting for months! The interviewer seemed really impressed with my portfolio and we had a great conversation about the company's future projects. I'm so excited about the possibility of working there!",
                "tags": ["career", "interview", "opportunity"],
                "expected_emotions": ["excited", "happy", "content"]
            }
        ]
        
        # Create test entries
        created_entries = []
        for entry_data in test_entries_data:
            entry = self.test_create_entry(
                entry_data["title"],
                entry_data["content"],
                entry_data["tags"],
                entry_data["expected_emotions"]
            )
            if entry:
                created_entries.append(entry)
            time.sleep(2)  # Brief pause between AI calls
        
        # Test getting all entries
        all_entries = self.test_get_entries()
        
        # Test getting specific entries
        if created_entries:
            self.test_get_entry_by_id(created_entries[0]["id"])
            
            # Test updating an entry
            updated_entry = self.test_update_entry(
                created_entries[0]["id"],
                "Updated: Amazing Day at the Beach",
                "Updated content: Today was absolutely wonderful! I spent the entire day at the beach with my family. The sun was shining, the waves were perfect, and we had such a great time building sandcastles and swimming. I feel so grateful and happy right now. Life is beautiful! UPDATE: Just got home and still feeling amazing!",
                ["family", "beach", "vacation", "updated"]
            )
        
        # Test getting non-existent entry
        self.test_get_entry_by_id("non-existent-id")
        
        print("\n=== Testing Weekly Mood Trends ===")
        self.test_weekly_mood_trends()
        
        print("\n=== Testing Tags Management ===")
        self.test_tags_management()
        
        # Clean up - delete test entries (except one for trend testing)
        print("\n=== Cleaning Up Test Data ===")
        if created_entries:
            for i, entry in enumerate(created_entries[1:], 1):  # Keep first entry
                self.test_delete_entry(entry["id"])
        
        # Test deleting non-existent entry
        self.test_delete_entry("non-existent-id")
        
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_passed = 0
        total_failed = 0
        
        for category, results in self.test_results.items():
            passed = results["passed"]
            failed = results["failed"]
            total_passed += passed
            total_failed += failed
            
            status = "✅" if failed == 0 else "❌"
            print(f"\n{status} {category.upper().replace('_', ' ')}: {passed} passed, {failed} failed")
            
            if results["details"]:
                for detail in results["details"]:
                    print(f"  {detail}")
        
        print(f"\n🎯 OVERALL RESULTS: {total_passed} passed, {total_failed} failed")
        
        if total_failed == 0:
            print("🎉 ALL TESTS PASSED!")
        else:
            print(f"⚠️  {total_failed} TESTS FAILED - Review details above")

if __name__ == "__main__":
    tester = JournalAPITester()
    tester.run_comprehensive_tests()