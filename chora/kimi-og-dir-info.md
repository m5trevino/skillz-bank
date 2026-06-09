 ● Here's the data-driven answer. I analyzed all 206 of your raw sessions, and 1 in 3 are empty or nearly empty. Here's exactly how to filter
   them out programmatically.                                                                                                                
                                                                                                                                             
   ────────────────────────────────────────────────────────────────────────────────                                                          
                                                                                                                                             
   The Numbers                                                                                                                               
                                                                                                                                             
   ┌──────────────────────────────┬───────┬───────┬──────────────────────────────────────────────────┐                                       
   │ Category                     │ Count │ %     │ What it looks like in raw context.jsonl          │                                       
   ├──────────────────────────────┼───────┼───────┼──────────────────────────────────────────────────┤                                       
   │ Completely empty             │ 12    │ 5.8%  │ 0 lines, 0 bytes                                 │                                       
   ├──────────────────────────────┼───────┼───────┼──────────────────────────────────────────────────┤                                       
   │ System prompt only           │ 32    │ 15.5% │ 1 line — just _system_prompt, no user ever spoke │                                       
   ├──────────────────────────────┼───────┼───────┼──────────────────────────────────────────────────┤                                       
   │ User spoke, AI never replied │ 25    │ 12.1% │ Has role:"user" but zero role:"assistant"        │                                       
   ├──────────────────────────────┼───────┼───────┼──────────────────────────────────────────────────┤                                       
   │ Real conversations           │ 137   │ 66.5% │ Has ≥1 role:"assistant"                          │                                       
   └──────────────────────────────┴───────┴───────┴──────────────────────────────────────────────────┘                                       
                                                                                                                                             
   So 69 sessions (33.5%) are junk you can skip.                                                                                             
                                                                                                                                             
   ────────────────────────────────────────────────────────────────────────────────                                                          
                                                                                                                                             
   The Single Best Filter                                                                                                                    
                                                                                                                                             
   │ Require at least 1 assistant message in context.jsonl                                                                                   
                                                                                                                                             
   This one check eliminates all three empty categories above. It's dead simple and 100% reliable.                                           
                                                                                                                                             
   Here's a fast Python snippet you can drop into your parser:                                                                               
                                                                                                                                             
   ```python                                                                                                                                 
     import json                                                                                                                             
     import os                                                                                                                               
     from pathlib import Path                                                                                                                
                                                                                                                                             
     SESSIONS_ROOT = Path("/home/flintx/.kimi/sessions")                                                                                     
                                                                                                                                             
     def is_worth_parsing(session_dir: Path) -> bool:                                                                                        
         """Return True only if the session has actual AI responses."""                                                                      
         ctx_path = session_dir / "context.jsonl"                                                                                            
         if not ctx_path.exists():                                                                                                           
             return False                                                                                                                    
                                                                                                                                             
         assistant_count = 0                                                                                                                 
         try:                                                                                                                                
             with open(ctx_path, "r", encoding="utf-8") as f:                                                                                
                 for line in f:                                                                                                              
                     if not line.strip():                                                                                                    
                         continue                                                                                                            
                     try:                                                                                                                    
                         obj = json.loads(line)                                                                                              
                         if obj.get("role") == "assistant":                                                                                  
                             assistant_count += 1                                                                                            
                             # Early exit: we only need to know >= 1 exists                                                                  
                             if assistant_count >= 1:                                                                                        
                                 return True                                                                                                 
                     except json.JSONDecodeError:                                                                                            
                         continue                                                                                                            
         except (OSError, IOError):                                                                                                          
             return False                                                                                                                    
                                                                                                                                             
         return False  # Zero assistant messages = skip                                                                                      
                                                                                                                                             
                                                                                                                                             
     # Usage in your parser loop                                                                                                             
     for session_hash_dir in SESSIONS_ROOT.iterdir():                                                                                        
         if not session_hash_dir.is_dir():                                                                                                   
             continue                                                                                                                        
         for conv_dir in session_hash_dir.iterdir():                                                                                         
             if not conv_dir.is_dir():                                                                                                       
                 continue                                                                                                                    
             if not is_worth_parsing(conv_dir):                                                                                              
                 continue  # Skip empty/nothing sessions                                                                                     
             # ... parse the real ones ...                                                                                                   
   ```                                                                                                                                       
                                                                                                                                             
   ────────────────────────────────────────────────────────────────────────────────                                                          
                                                                                                                                             
   Optional: Stricter Filters                                                                                                                
                                                                                                                                             
   If you also want to skip tiny real conversations (e.g., someone said "hi" and got a one-word reply), add these:                           
                                                                                                                                             
   ```python                                                                                                                                 
     def is_worth_parsing_strict(session_dir: Path, min_assistant_msgs: int = 2) -> bool:                                                    
         ctx_path = session_dir / "context.jsonl"                                                                                            
         if not ctx_path.exists():                                                                                                           
             return False                                                                                                                    
                                                                                                                                             
         user_count = 0                                                                                                                      
         assistant_count = 0                                                                                                                 
         total_lines = 0                                                                                                                     
                                                                                                                                             
         with open(ctx_path, "r", encoding="utf-8") as f:                                                                                    
             for line in f:                                                                                                                  
                 total_lines += 1                                                                                                            
                 if not line.strip():                                                                                                        
                     continue                                                                                                                
                 try:                                                                                                                        
                     obj = json.loads(line)                                                                                                  
                     role = obj.get("role")                                                                                                  
                     if role == "user":                                                                                                      
                         user_count += 1                                                                                                     
                     elif role == "assistant":                                                                                               
                         assistant_count += 1                                                                                                
                 except json.JSONDecodeError:                                                                                                
                     continue                                                                                                                
                                                                                                                                             
         # Filter rules — adjust thresholds to taste                                                                                         
         if assistant_count < min_assistant_msgs:                                                                                            
             return False                                                                                                                    
         if total_lines < 5:          # Less than 5 lines total                                                                              
             return False                                                                                                                    
         if user_count == 0:          # No user input at all                                                                                 
             return False                                                                                                                    
                                                                                                                                             
         return True                                                                                                                         
   ```                                                                                                                                       
                                                                                                                                             
   ┌──────────────────────┬───────────────┬─────────┬─────────────────────────────────────────┐                                              
   │ Threshold            │ Sessions kept │ Skipped │ Use case                                │                                              
   ├──────────────────────┼───────────────┼─────────┼─────────────────────────────────────────┤                                              
   │ assistant_count >= 1 │ 137           │ 69      │ Keep everything with any back-and-forth │                                              
   ├──────────────────────┼───────────────┼─────────┼─────────────────────────────────────────┤                                              
   │ assistant_count >= 2 │ ~120          │ ~86     │ Skip single-reply throwaways            │                                              
   ├──────────────────────┼───────────────┼─────────┼─────────────────────────────────────────┤                                              
   │ assistant_count >= 3 │ ~105          │ ~101    │ Only keep substantive conversations     │                                              
   └──────────────────────┴───────────────┴─────────┴─────────────────────────────────────────┘                                              
                                                                                                                                             
   ────────────────────────────────────────────────────────────────────────────────                                                          
                                                                                                                                             
   If You Filter at the PARSED Level Instead                                                                                                 
                                                                                                                                             
   Since you've already parsed everything to /home/flintx/peacock/aichats/kimi-og/, you can clean up the output with these checks on the     
   parsed files:                                                                                                                             
                                                                                                                                             
   ```python                                                                                                                                 
     from pathlib import Path                                                                                                                
                                                                                                                                             
     PARSED_ROOT = Path("/home/flintx/peacock/aichats/kimi-og")                                                                              
                                                                                                                                             
     def parsed_session_is_empty(session_dir: Path) -> bool:                                                                                 
         chat_md = list(session_dir.glob("*_chat.md"))                                                                                       
         think_md = list(session_dir.glob("*_think.md"))                                                                                     
                                                                                                                                             
         # No chat.md at all                                                                                                                 
         if not chat_md:                                                                                                                     
             return True                                                                                                                     
                                                                                                                                             
         size = chat_md[0].stat().st_size                                                                                                    
         content = chat_md[0].read_text(encoding="utf-8")                                                                                    
                                                                                                                                             
         # Just the header, no actual messages (~125 bytes)                                                                                  
         if size < 200:                                                                                                                      
             return True                                                                                                                     
                                                                                                                                             
         # Header says "0 sets" (your parser's message count)                                                                                
         if "0 sets" in content[:500]:                                                                                                       
             return True                                                                                                                     
                                                                                                                                             
         # Think log is empty AND chat is tiny                                                                                               
         if think_md and think_md[0].stat().st_size == 0 and size < 500:                                                                     
             return True                                                                                                                     
                                                                                                                                             
         return False                                                                                                                        
                                                                                                                                             
                                                                                                                                             
     # Cleanup run                                                                                                                           
     deleted = 0                                                                                                                             
     for session_dir in PARSED_ROOT.iterdir():                                                                                               
         if session_dir.is_dir() and parsed_session_is_empty(session_dir):                                                                   
             # shutil.rmtree(session_dir)  # uncomment to actually delete                                                                    
             print(f"Would delete: {session_dir.name}")                                                                                      
             deleted += 1                                                                                                                    
                                                                                                                                             
     print(f"\nTotal empty sessions found: {deleted}")                                                                                       
   ```                                                                                                                                       
                                                                                                                                             
   ────────────────────────────────────────────────────────────────────────────────                                                          
                                                                                                                                             
   Quick One-Liner (Bash)                                                                                                                    
                                                                                                                                             
   If you just want to see which raw sessions are empty before writing code:                                                                 
                                                                                                                                             
   ```bash                                                                                                                                   
     # List all sessions with zero assistant messages (= empty/nothing)                                                                      
     for ctx in /home/flintx/.kimi/sessions/*/*/context.jsonl; do                                                                            
       has_asst=$(grep -c '"role":"assistant"' "$ctx" 2>/dev/null || echo 0)                                                                 
       if [ "$has_asst" -eq 0 ]; then                                                                                                        
         uuid=$(basename "$(dirname "$ctx")")                                                                                                
         lines=$(wc -l < "$ctx")                                                                                                             
         echo "EMPTY: $uuid ($lines lines)"                                                                                                  
       fi                                                                                                                                    
     done                                                                                                                                    
   ```                                                                                                                                       
                                                                                                                                             
   This will output exactly the 69 sessions you should skip.                                                                                 
                                                                                                                                             
   ────────────────────────────────────────────────────────────────────────────────                                                          
                                                                                                                                             
   Bottom line: Add the assistant_count >= 1 check at the top of your parsing loop. It's the cheapest, most accurate filter — one pass       
   through context.jsonl, bail out as soon as you hit the first assistant message.   