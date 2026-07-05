import customtkinter as ctk
import threading
import time
import io
import urllib.request
from PIL import Image
from pathlib import Path

from zenmetabot.config import CFG, log
from zenmetabot.youtube import get_youtube_client
from zenmetabot.orchestrator import process_single_video
from zenmetabot.progress import progress

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class Zen MetaBotApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Zen MetaBot Bot v2.0 - Multi-AI Debate Engine")
        self.geometry("1100x700")

        self.videos = []
        self.selection_vars = []
        self.is_running = False
        self.stop_requested = False
        self.all_selected = True

        # Create Tabview
        self.tabview = ctk.CTkTabview(self, width=1050, height=650)
        self.tabview.pack(padx=20, pady=20, fill="both", expand=True)

        self.tab_dash = self.tabview.add("📋 Dashboard")
        self.tab_debate = self.tabview.add("⚔️ Debate Viewer")
        self.tab_settings = self.tabview.add("⚙️ Settings")

        self.build_settings_tab()
        self.build_dashboard_tab()
        self.build_debate_tab()

    def build_settings_tab(self):
        frame = ctk.CTkScrollableFrame(self.tab_settings)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(frame, text="API Keys", font=("Arial", 16, "bold")).pack(anchor="w", pady=(10,5))
        
        self.nv_api_var = ctk.StringVar(value=CFG.NVIDIA_API_KEY)
        ctk.CTkLabel(frame, text="NVIDIA API Key:").pack(anchor="w")
        ctk.CTkEntry(frame, textvariable=self.nv_api_var, width=600, show="*").pack(anchor="w", pady=(0, 10))

        self.gem_api_var = ctk.StringVar(value=CFG.GEMINI_API_KEY)
        ctk.CTkLabel(frame, text="Gemini API Key:").pack(anchor="w")
        ctk.CTkEntry(frame, textvariable=self.gem_api_var, width=600, show="*").pack(anchor="w", pady=(0, 10))

        ctk.CTkLabel(frame, text="Generation Mode", font=("Arial", 16, "bold")).pack(anchor="w", pady=(20,5))
        self.mode_var = ctk.StringVar(value=CFG.GENERATION_MODE)
        ctk.CTkRadioButton(frame, text="NVIDIA Solo", variable=self.mode_var, value="nvidia").pack(anchor="w", pady=5)
        ctk.CTkRadioButton(frame, text="Gemini Solo", variable=self.mode_var, value="gemini").pack(anchor="w", pady=5)
        ctk.CTkRadioButton(frame, text="⚔️ DEBATE MODE (Ultimate)", variable=self.mode_var, value="debate").pack(anchor="w", pady=5)

        ctk.CTkLabel(frame, text="Video Filter", font=("Arial", 16, "bold")).pack(anchor="w", pady=(20,5))
        self.filter_var = ctk.StringVar(value=CFG.VIDEO_TYPE_FILTER)
        ctk.CTkRadioButton(frame, text="All Videos", variable=self.filter_var, value="all").pack(anchor="w", pady=5)
        ctk.CTkRadioButton(frame, text="Shorts Only", variable=self.filter_var, value="shorts").pack(anchor="w", pady=5)
        ctk.CTkRadioButton(frame, text="Longs Only", variable=self.filter_var, value="longs").pack(anchor="w", pady=5)
        
        ctk.CTkLabel(frame, text="Brain Extraction Mode", font=("Arial", 16, "bold")).pack(anchor="w", pady=(20,5))
        self.rewatch_var = ctk.BooleanVar(value=CFG.FORCE_REWATCH)
        ctk.CTkRadioButton(frame, text="Smart Meta (Use existing Brain)", variable=self.rewatch_var, value=False).pack(anchor="w", pady=5)
        ctk.CTkRadioButton(frame, text="Force Rewatch (Extract new Brain)", variable=self.rewatch_var, value=True).pack(anchor="w", pady=5)

        ctk.CTkButton(frame, text="💾 Save to .env", command=self.save_settings, fg_color="green").pack(anchor="w", pady=30)

    def save_settings(self):
        env_path = Path(".env")
        if not env_path.exists():
            env_path.write_text("")
            
        content = env_path.read_text()
        
        # Simple string replacement for save (in a real app, use python-dotenv set_key)
        import re
        def update_or_add(key, val, text):
            if re.search(rf"^{key}=", text, flags=re.M):
                return re.sub(rf"^{key}=.*", f"{key}={val}", text, flags=re.M)
            else:
                return text + f"\n{key}={val}"

        content = update_or_add("NVIDIA_API_KEY", self.nv_api_var.get(), content)
        content = update_or_add("GEMINI_API_KEY", self.gem_api_var.get(), content)
        content = update_or_add("GENERATION_MODE", self.mode_var.get(), content)
        content = update_or_add("VIDEO_TYPE_FILTER", self.filter_var.get(), content)
        content = update_or_add("FORCE_REWATCH", str(self.rewatch_var.get()).lower(), content)

        env_path.write_text(content)
        
        CFG.NVIDIA_API_KEY = self.nv_api_var.get()
        CFG.GEMINI_API_KEY = self.gem_api_var.get()
        CFG.GENERATION_MODE = self.mode_var.get()
        CFG.VIDEO_TYPE_FILTER = self.filter_var.get()
        CFG.FORCE_REWATCH = self.rewatch_var.get()
        
        self.log_debate("Settings saved successfully!")

    def build_dashboard_tab(self):
        # Top bar
        top_bar = ctk.CTkFrame(self.tab_dash, fg_color="transparent")
        top_bar.pack(fill="x", padx=10, pady=10)

        ctk.CTkButton(top_bar, text="🔄 Fetch Videos", command=self.fetch_videos_thread).pack(side="left", padx=5)
        self.btn_select_all = ctk.CTkButton(top_bar, text="☑ Select All", command=self.toggle_select_all, state="disabled", fg_color="gray", width=100)
        self.btn_select_all.pack(side="left", padx=5)
        self.btn_start = ctk.CTkButton(top_bar, text="▶ Start Processing", command=self.start_processing, fg_color="green", state="disabled")
        self.btn_start.pack(side="left", padx=5)
        self.btn_stop = ctk.CTkButton(top_bar, text="⏹ Stop", command=self.stop_processing, fg_color="red", state="disabled")
        self.btn_stop.pack(side="left", padx=5)
        
        self.lbl_status = ctk.CTkLabel(top_bar, text="Status: Idle", font=("Arial", 12, "italic"))
        self.lbl_status.pack(side="right", padx=10)

        # Video List area
        self.scroll_frame = ctk.CTkScrollableFrame(self.tab_dash, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Progress
        self.prog_bar = ctk.CTkProgressBar(self.tab_dash)
        self.prog_bar.pack(fill="x", padx=10, pady=(0, 10))
        self.prog_bar.set(0)

    def toggle_select_all(self):
        self.all_selected = not self.all_selected
        for var in self.selection_vars:
            var.set(self.all_selected)
        self.btn_select_all.configure(text="☑ Deselect All" if self.all_selected else "☑ Select All")

    def build_debate_tab(self):
        self.debate_log = ctk.CTkTextbox(self.tab_debate, state="normal", wrap="word", font=("Consolas", 13))
        self.debate_log.pack(fill="both", expand=True, padx=10, pady=10)
        self.debate_log.configure(state="disabled")

    def log_debate(self, text):
        self.debate_log.configure(state="normal")
        self.debate_log.insert("end", text + "\n")
        self.debate_log.see("end")
        self.debate_log.configure(state="disabled")
        self.update()

    def fetch_videos_thread(self):
        self.lbl_status.configure(text="Status: Fetching videos from YouTube...")
        self.btn_select_all.configure(state="disabled")
        threading.Thread(target=self._fetch_videos, daemon=True).start()

    def _fetch_videos(self):
        try:
            self.videos = get_youtube_client().get_videos()
            self.lbl_status.configure(text=f"Status: Loaded {len(self.videos)} videos. Loading thumbnails...")
            self.update_listbox()
            self.lbl_status.configure(text=f"Status: Ready. ({len(self.videos)} videos found)")
            self.btn_start.configure(state="normal")
            self.btn_select_all.configure(state="normal")
        except Exception as e:
            self.lbl_status.configure(text=f"Error: {e}")
            self.log_debate(f"Fetch Error: {e}")

    def get_thumbnail(self, video_id):
        try:
            url = f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = resp.read()
            img = Image.open(io.BytesIO(data))
            # Resize slightly for UI
            img.thumbnail((160, 90))
            return ctk.CTkImage(light_image=img, dark_image=img, size=(160, 90))
        except Exception as e:
            log.warning(f"Failed to fetch thumbnail for {video_id}: {e}")
            return None

    def update_listbox(self):
        # Clear existing
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
            
        self.selection_vars.clear()

        for v in self.videos:
            var = ctk.BooleanVar(value=True)
            self.selection_vars.append(var)
            
            card = ctk.CTkFrame(self.scroll_frame, fg_color="#1E1E1E", corner_radius=10)
            card.pack(fill="x", padx=5, pady=5)
            
            cb = ctk.CTkCheckBox(card, text="", variable=var, width=30)
            cb.pack(side="left", padx=10)
            
            # Fetch and display thumbnail
            thumb_img = self.get_thumbnail(v.id)
            if thumb_img:
                lbl_img = ctk.CTkLabel(card, text="", image=thumb_img)
                lbl_img.pack(side="left", padx=10, pady=10)
                
            # Details frame
            details = ctk.CTkFrame(card, fg_color="transparent")
            details.pack(side="left", fill="both", expand=True, padx=10, pady=10)
            
            ctk.CTkLabel(details, text=v.old_title, font=("Arial", 14, "bold"), anchor="w").pack(fill="x")
            
            vtype = "Short" if v.duration_s <= CFG.MAX_DURATION_S else "Long"
            done_text = "✅ Processed" if progress.is_done(v.id) else "⏳ Pending"
            info_text = f"ID: {v.id}  •  {vtype}  •  {v.duration_s}s  •  {done_text}"
            
            ctk.CTkLabel(details, text=info_text, font=("Arial", 12), text_color="gray", anchor="w").pack(fill="x")

    def start_processing(self):
        if not self.videos:
            return
        self.is_running = True
        self.stop_requested = False
        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.lbl_status.configure(text="Status: Processing...")
        self.tabview.set("⚔️ Debate Viewer")
        
        threading.Thread(target=self._process_queue, daemon=True).start()

    def stop_processing(self):
        self.stop_requested = True
        self.lbl_status.configure(text="Status: Stopping (Waiting for current video to finish)...")
        self.btn_stop.configure(state="disabled")

    def _process_queue(self):
        # Filter selected videos
        selected_videos = [v for i, v in enumerate(self.videos) if self.selection_vars[i].get()]
        total = len(selected_videos)
        
        if total == 0:
            self.log_debate("\n❌ No videos selected for processing.")
            self.is_running = False
            self.btn_start.configure(state="normal")
            self.btn_stop.configure(state="disabled")
            self.lbl_status.configure(text="Status: Finished.")
            return

        success_count = 0
        for i, v in enumerate(selected_videos, 1):
            if self.stop_requested:
                self.log_debate("\n⏹ Processing stopped by user.")
                break
                
            self.prog_bar.set(i / total)
            
            ok = process_single_video(v, i, total, skip_done=CFG.SKIP_DONE, gui_callback=self.log_debate)
            if ok:
                success_count += 1
                
            # Update the specific card visually if needed, but for now we just rely on the log
            # Since thumbnails take time to fetch, we won't redraw the whole list here
            
            if i < total and not self.stop_requested and not (CFG.SKIP_DONE and progress.is_done(v.id)):
                self.log_debate(f"  [Waiting {CFG.INTER_VIDEO_S}s for rate limits...]")
                time.sleep(CFG.INTER_VIDEO_S)
                
        self.is_running = False
        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        self.lbl_status.configure(text=f"Status: Finished. ({success_count}/{total} successful)")

def launch_gui():
    app = Zen MetaBotApp()
    app.mainloop()

if __name__ == "__main__":
    launch_gui()
