 ● The script is ready. Here's the breakdown of what makes sessions "empty" and how to filter them:                                          
                                                                                                                                             
   ────────────────────────────────────────────────────────────────────────────────                                                          
                                                                                                                                             
   What Makes a Session "Empty" or "Near-Empty"                                                                                              
                                                                                                                                             
   Based on your 239 source files, 124 are junk and 115 are worth keeping. The junk falls into these categories:                             
                                                                                                                                             
   ┌──────────────────┬──────────────────────────────────────────────┬────────────────────────────────────────────────────────────┐          
   │ Category         │ Cause                                        │ Example                                                    │          
   ├──────────────────┼──────────────────────────────────────────────┼────────────────────────────────────────────────────────────┤          
   │ Dead JSONL       │ Metadata line only, no messages              │ session-2026-05-20T12-48-07c4b7c4.jsonl → 1 line, 0 msgs   │          
   ├──────────────────┼──────────────────────────────────────────────┼────────────────────────────────────────────────────────────┤          
   │ No bot responses │ User sent messages but Gemini never replied  │ session-2026-05-11T10-04-091f79f2.jsonl → 2 user, 0 gemini │          
   ├──────────────────┼──────────────────────────────────────────────┼────────────────────────────────────────────────────────────┤          
   │ logs.json only   │ Legacy format with only user command history │ logs.json → user msgs only, no model responses ever        │          
   ├──────────────────┼──────────────────────────────────────────────┼────────────────────────────────────────────────────────────┤          
   │ Sub-agent duds   │ Sub-agent spawned but did nothing            │ 0x9a6m.jsonl, 21lp5q.jsonl → 0 gemini msgs                 │          
   ├──────────────────┼──────────────────────────────────────────────┼────────────────────────────────────────────────────────────┤          
   │ Too short        │ A few messages but almost no content         │ session-2026-05-10T05-51-5cc63d15.jsonl → 28 chars total   │          
   └──────────────────┴──────────────────────────────────────────────┴────────────────────────────────────────────────────────────┘          
                                                                                                                                             
   ────────────────────────────────────────────────────────────────────────────────                                                          
                                                                                                                                             
   The Script                                                                                                                                
                                                                                                                                             
   I wrote /home/flintx/peacock/aichats/gemini-cli/filter_empty_sessions.py. It handles all 3 source formats and calculates these metrics per
   file:                                                                                                                                     
                                                                                                                                             
   • user_count — how many user messages                                                                                                     
   • gemini_count — how many bot responses (the key filter!)                                                                                 
   • total_content_chars — actual text content length                                                                                        
   • has_thoughts / has_tool_calls — richness flags                                                                                          
                                                                                                                                             
   Standalone usage:                                                                                                                         
                                                                                                                                             
   ```bash                                                                                                                                   
     # Basic run                                                                                                                             
     python3 filter_empty_sessions.py                                                                                                        
                                                                                                                                             
     # See what's being skipped and why                                                                                                      
     python3 filter_empty_sessions.py --report                                                                                               
                                                                                                                                             
     # Stricter: require at least 3 bot responses                                                                                            
     python3 filter_empty_sessions.py --min-gemini 3                                                                                         
                                                                                                                                             
     # Export only the good files to a list                                                                                                  
     python3 filter_empty_sessions.py --export-good good_sessions.txt                                                                        
   ```                                                                                                                                       
                                                                                                                                             
   Integrate into your existing parser:                                                                                                      
                                                                                                                                             
   ```python                                                                                                                                 
     from filter_empty_sessions import is_session_worth_parsing, scan_sessions                                                               
                                                                                                                                             
     # Quick check on a single file before parsing                                                                                           
     path = Path("/home/flintx/.gemini/tmp/doc-dumpster/chats/session-xxx.jsonl")                                                            
     is_good, info = is_session_worth_parsing(path)                                                                                          
                                                                                                                                             
     if not is_good:                                                                                                                         
         print(f"Skipping: {info.skip_reason}")                                                                                              
         continue                                                                                                                            
                                                                                                                                             
     # Or batch-scan everything upfront                                                                                                      
     good_sessions = [                                                                                                                       
         s for s in scan_sessions()                                                                                                          
         if s.is_worth_parsing                                                                                                               
     ]                                                                                                                                       
                                                                                                                                             
     for s in good_sessions:                                                                                                                 
         print(s.source_path)  # Parse these only                                                                                            
   ```                                                                                                                                       
                                                                                                                                             
   ────────────────────────────────────────────────────────────────────────────────                                                          
                                                                                                                                             
   Default Thresholds (tune as needed)                                                                                                       
                                                                                                                                             
   ```python                                                                                                                                 
     MIN_USER_MSGS    = 1   # At least 1 user message                                                                                        
     MIN_GEMINI_MSGS  = 1   # At least 1 bot response ← THIS is the killer filter                                                            
     MIN_TOTAL_MSGS   = 3   # At least 3 total messages                                                                                      
     MIN_CONTENT_CHARS = 50 # At least 50 chars of content                                                                                   
   ```                                                                                                                                       
                                                                                                                                             
   The most important filter is MIN_GEMINI_MSGS = 1. If there are zero bot responses, the session produced nothing worth parsing — this alone
   catches ~90% of the junk.                                                                                                                 
                                                                                                                                             
   ────────────────────────────────────────────────────────────────────────────────                                                          
                                                                                                                                             
   Your Numbers                                                                                                                              
                                                                                                                                             
   ┌─────────────────────────┬───────────────────────────────────┐                                                                           
   │ Metric                  │ Count                             │                                                                           
   ├─────────────────────────┼───────────────────────────────────┤                                                                           
   │ Total source files      │ 239                               │                                                                           
   ├─────────────────────────┼───────────────────────────────────┤                                                                           
   │ Good sessions           │ 115                               │                                                                           
   ├─────────────────────────┼───────────────────────────────────┤                                                                           
   │ Skipped (empty/junk)    │ 124                               │                                                                           
   ├─────────────────────────┼───────────────────────────────────┤                                                                           
   │ Largest good session    │ 1,336 gemini msgs / 918,838 chars │                                                                           
   ├─────────────────────────┼───────────────────────────────────┤                                                                           
   │ Most common skip reason │ only 0 gemini msg(s)              │                                                                           
   └─────────────────────────┴───────────────────────────────────┘  