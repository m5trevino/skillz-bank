 ● Here's the full forensic picture and the exact code to fix it.                                                                            
                                                                                                                                             
   What I Found                                                                                                                              
                                                                                                                                             
   ┌─────────────┬───────┬──────────────────────────────────────────────────────────────────────────────────────┐                            
   │ Category    │ Count │ Description                                                                          │                            
   ├─────────────┼───────┼──────────────────────────────────────────────────────────────────────────────────────┤                            
   │ Truly empty │ 60    │ ≤5 lines, zero tool activity. Metadata + a "whats up" or single paste, nothing else. │                            
   ├─────────────┼───────┼──────────────────────────────────────────────────────────────────────────────────────┤                            
   │ Chat-only   │ 1     │ 14 lines, zero tools. Just conversation, no files touched.                           │                            
   ├─────────────┼───────┼──────────────────────────────────────────────────────────────────────────────────────┤                            
   │ Real work   │ 184   │ At least one tool was invoked (file read, write, shell, etc.)                        │                            
   └─────────────┴───────┴──────────────────────────────────────────────────────────────────────────────────────┘                            
                                                                                                                                             
   The key insight: The single best signal is whether the assistant ever used a tool. If tool_calls == 0 and tool_result_msgs == 0, the      
   session produced nothing actionable — no files read, no code written, no commands run.                                                    
                                                                                                                                             
   ────────────────────────────────────────────────────────────────────────────────                                                          
                                                                                                                                             
   Drop-in Python Filter                                                                                                                     
                                                                                                                                             
   Add this function to your parser. It handles both old and new wire protocol versions.                                                     
                                                                                                                                             
   ```python                                                                                                                                 
     import json                                                                                                                             
     from pathlib import Path                                                                                                                
                                                                                                                                             
                                                                                                                                             
     def is_meaningful_session(wire_jsonl_path: Path, min_lines: int = 6, require_tools: bool = True) -> bool:                               
         """                                                                                                                                 
         Returns True if a wire.jsonl has enough substance to be worth parsing.                                                              
                                                                                                                                             
         Parameters                                                                                                                          
         ----------                                                                                                                          
         wire_jsonl_path : Path                                                                                                              
             Path to agents/{id}/wire.jsonl                                                                                                  
         min_lines : int                                                                                                                     
             Minimum number of JSONL events. Default 6 catches all the 2-5 line                                                              
             metadata-only sessions.                                                                                                         
         require_tools : bool                                                                                                                
             If True, requires at least one tool call or tool result message.                                                                
             This filters out pure chat sessions where the assistant only                                                                    
             replied with text (e.g. "whats up" → "not much").                                                                               
         """                                                                                                                                 
         lines = 0                                                                                                                           
         has_tools = False                                                                                                                   
                                                                                                                                             
         with open(wire_jsonl_path, "r", encoding="utf-8") as f:                                                                             
             for raw in f:                                                                                                                   
                 lines += 1                                                                                                                  
                 raw = raw.strip()                                                                                                           
                 if not raw:                                                                                                                 
                     continue                                                                                                                
                 try:                                                                                                                        
                     obj = json.loads(raw)                                                                                                   
                     t = obj.get("type", "")                                                                                                 
                                                                                                                                             
                     # Newer protocol: tool calls appear as loop events                                                                      
                     if t == "context.append_loop_event":                                                                                    
                         event = obj.get("event", {})                                                                                        
                         if event.get("type") == "tool.call":                                                                                
                             has_tools = True                                                                                                
                                                                                                                                             
                     # Older protocol: tool results appear directly as messages                                                              
                     elif t == "context.append_message":                                                                                     
                         if obj.get("message", {}).get("role") == "tool":                                                                    
                             has_tools = True                                                                                                
                                                                                                                                             
                 except json.JSONDecodeError:                                                                                                
                     continue                                                                                                                
                                                                                                                                             
         if lines < min_lines:                                                                                                               
             return False                                                                                                                    
         if require_tools and not has_tools:                                                                                                 
             return False                                                                                                                    
         return True                                                                                                                         
                                                                                                                                             
                                                                                                                                             
     # === USAGE IN YOUR PARSER LOOP ===                                                                                                     
                                                                                                                                             
     SESSIONS_ROOT = Path.home() / ".kimi-code" / "sessions"                                                                                 
                                                                                                                                             
     for wire_path in SESSIONS_ROOT.rglob("agents/*/wire.jsonl"):                                                                            
         if not is_meaningful_session(wire_path):                                                                                            
             print(f"SKIP (empty): {wire_path}")                                                                                             
             continue                                                                                                                        
                                                                                                                                             
         # ... your existing parse logic ...                                                                                                 
         print(f"PARSE: {wire_path}")                                                                                                        
   ```                                                                                                                                       
                                                                                                                                             
   ────────────────────────────────────────────────────────────────────────────────                                                          
                                                                                                                                             
   Three Preset Strictness Levels                                                                                                            
                                                                                                                                             
   ```python                                                                                                                                 
     # 1. LENIENT — skips only the 60 truly dead sessions                                                                                    
     #    (metadata + one-line "whats up" with no reply)                                                                                     
     if is_meaningful_session(wire_path, min_lines=6, require_tools=False):                                                                  
         ...                                                                                                                                 
                                                                                                                                             
     # 2. RECOMMENDED — skips 61 sessions (the 60 dead + 1 chat-only)                                                                        
     #    Keeps 184 sessions where the assistant actually DID something                                                                      
     if is_meaningful_session(wire_path, min_lines=6, require_tools=True):                                                                   
         ...                                                                                                                                 
                                                                                                                                             
     # 3. STRICT — only keep substantial multi-turn work sessions                                                                            
     #    Skips 69 sessions, keeps 176                                                                                                       
     if is_meaningful_session(wire_path, min_lines=10, require_tools=True):                                                                  
         ...                                                                                                                                 
   ```                                                                                                                                       
                                                                                                                                             
   ────────────────────────────────────────────────────────────────────────────────                                                          
                                                                                                                                             
   Quick CLI Sanity Check                                                                                                                    
                                                                                                                                             
   Run this to preview what your filter would skip vs keep:                                                                                  
                                                                                                                                             
   ```bash                                                                                                                                   
     python3 << 'PYEOF'                                                                                                                      
     import json                                                                                                                             
     from pathlib import Path                                                                                                                
                                                                                                                                             
     root = Path.home() / ".kimi-code" / "sessions"                                                                                          
     skipped = []                                                                                                                            
     kept = []                                                                                                                               
                                                                                                                                             
     for p in root.rglob("agents/*/wire.jsonl"):                                                                                             
         lines = 0                                                                                                                           
         has_tools = False                                                                                                                   
         with open(p) as f:                                                                                                                  
             for line in f:                                                                                                                  
                 lines += 1                                                                                                                  
                 try:                                                                                                                        
                     obj = json.loads(line.strip())                                                                                          
                     t = obj.get("type", "")                                                                                                 
                     if t == "context.append_loop_event" and obj.get("event", {}).get("type") == "tool.call":                                
                         has_tools = True                                                                                                    
                     elif t == "context.append_message" and obj.get("message", {}).get("role") == "tool":                                    
                         has_tools = True                                                                                                    
                 except:                                                                                                                     
                     pass                                                                                                                    
                                                                                                                                             
         # RECOMMENDED filter                                                                                                                
         if lines < 6 or not has_tools:                                                                                                      
             skipped.append((lines, p))                                                                                                      
         else:                                                                                                                               
             kept.append((lines, p))                                                                                                         
                                                                                                                                             
     print(f"=== WOULD SKIP ({len(skipped)}) ===")                                                                                           
     for lines, p in sorted(skipped)[:15]:                                                                                                   
         print(f"  {lines:3d} lines  {p.name} in .../{p.parent.parent.parent.name}")                                                         
     print(f"  ... and {len(skipped)-15} more" if len(skipped) > 15 else "")                                                                 
                                                                                                                                             
     print(f"\n=== WOULD KEEP ({len(kept)}) ===")                                                                                            
     for lines, p in sorted(kept)[:10]:                                                                                                      
         print(f"  {lines:3d} lines  {p.name} in .../{p.parent.parent.parent.name}")                                                         
     print(f"  ... and {len(kept)-10} more" if len(kept) > 10 else "")                                                                       
     PYEOF                                                                                                                                   
   ```                                                                                                                                       
                                                                                                                                             
   ────────────────────────────────────────────────────────────────────────────────                                                          
                                                                                                                                             
   The One Weird Edge Case                                                                                                                   
                                                                                                                                             
   There is exactly 1 session with 14 lines and zero tools — it's a Chora session that only contains compaction context + a brief assistant  
   summary. The require_tools=True filter catches it automatically.                                                                          
                                                                                                                                             
   If you want to see it:                                                                                                                    
                                                                                                                                             
   ```                                                                                                                                       
     /home/flintx/.kimi-code/sessions/wd_chora_bd87ffe4001c/session_7ef8652f-82a3-4954-ba82-db0ad15892eb/agents/main/wire.jsonl              
   ```                                                                                                                                       
                                                                                                                                             
   ────────────────────────────────────────────────────────────────────────────────                                                          
                                                                                                                                             
   My recommendation: Use require_tools=True with min_lines=6. That skips 61 dead sessions (25% of your corpus) and keeps every session where
   the assistant actually touched a file or ran a command. No more empty outputs.   