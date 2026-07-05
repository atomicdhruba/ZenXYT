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

class ZenMetaBotApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Zen MetaBot v2.0 - Ultimate AI Dashboard")
        self.geometry("1200x750")
        
        # --- Premium Palette ---
        self.C_ACCENT = "#00E5FF" # Electric Cyan
        self.C_HOVER  = "#00B8D4"
        self.C_BG     = "#0F1015" # Deep Dark Space
        self.C_CARD   = "#16181F" # Slightly lighter card
        self.C_GREEN  = "#00E676"
        self.C_RED    = "#FF1744"

        self.configure(fg_color=self.C_BG)
        
        self.videos = []
        self.selection_vars = []
        self.is_running = False
        self.stop_requested = False
        self.all_selected = True

        # Grid Layout 1x2
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # 1. SIDEBAR
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color="#12131A")
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)

        self.sidebar_header = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.sidebar_header.grid(row=0, column=0, padx=20, pady=(30, 40))
        
        self.logo_label = ctk.CTkLabel(self.sidebar_header, text="Zen MetaBot", font=ctk.CTkFont(size=24, weight="bold"), text_color=self.C_ACCENT)
        self.logo_label.pack()
        
        self.lbl_dot = ctk.CTkLabel(self.sidebar_header, text="🟢 Online", font=ctk.CTkFont(size=12), text_color="gray60")
        self.lbl_dot.pack(pady=(5,0))

        # Navigation Buttons
        self.btn_nav_dash = ctk.CTkButton(self.sidebar_frame, corner_radius=8, height=40, border_spacing=10, text="📋 Dashboard",
                                        fg_color="transparent", text_color="gray90", hover_color="#2A2D3A", anchor="w",
                                        font=ctk.CTkFont(size=14, weight="bold"), command=self.show_dashboard)
        self.btn_nav_dash.grid(row=1, column=0, sticky="ew", padx=15, pady=5)
        
        self.btn_nav_debate = ctk.CTkButton(self.sidebar_frame, corner_radius=8, height=40, border_spacing=10, text="⚙️ AI Processing Logs",
                                        fg_color="transparent", text_color="gray90", hover_color="#2A2D3A", anchor="w",
                                        font=ctk.CTkFont(size=14, weight="bold"), command=self.show_debate)
        self.btn_nav_debate.grid(row=2, column=0, sticky="ew", padx=15, pady=5)
        
        self.btn_nav_settings = ctk.CTkButton(self.sidebar_frame, corner_radius=8, height=40, border_spacing=10, text="⚙️ Settings",
                                        fg_color="transparent", text_color="gray90", hover_color="#2A2D3A", anchor="w",
                                        font=ctk.CTkFont(size=14, weight="bold"), command=self.show_settings)
        self.btn_nav_settings.grid(row=3, column=0, sticky="ew", padx=15, pady=5)

        # 2. MAIN CONTAINER
        self.main_container = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_container.grid(row=0, column=1, sticky="nsew")
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)
        
        # Define Pages
        self.tab_dash = ctk.CTkFrame(self.main_container, corner_radius=0, fg_color="transparent")
        self.tab_debate = ctk.CTkFrame(self.main_container, corner_radius=0, fg_color="transparent")
        self.tab_settings = ctk.CTkFrame(self.main_container, corner_radius=0, fg_color="transparent")

        self.build_settings_tab()
        self.build_dashboard_tab()
        self.build_debate_tab()
        
        self.show_dashboard()
        
        # Spinner Animation
        self.spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.spinner_idx = 0
        self.animate_spinners()

    def animate_spinners(self):
        self.spinner_idx = (self.spinner_idx + 1) % len(self.spinner_frames)
        frame = self.spinner_frames[self.spinner_idx]
        
        if hasattr(self, "card_labels"):
            for v_id, lbl_dict in self.card_labels.items():
                lbl_info = lbl_dict["info"]
                text = lbl_info.cget("text")
                if "Pending" in text:
                    # The text is "ID: ... • Short • 30s • ⏳ Pending"
                    parts = text.rsplit("•", 1)
                    if len(parts) == 2:
                        lbl_info.configure(text=f"{parts[0]}•  {frame} Pending")
        
        self.after(100, self.animate_spinners)

    def select_frame_by_name(self, name):
        self.btn_nav_dash.configure(fg_color=("gray75", "gray25") if name == "dash" else "transparent")
        self.btn_nav_debate.configure(fg_color=("gray75", "gray25") if name == "debate" else "transparent")
        self.btn_nav_settings.configure(fg_color=("gray75", "gray25") if name == "settings" else "transparent")
        
        if name == "dash": self.tab_dash.grid(row=0, column=0, sticky="nsew")
        else: self.tab_dash.grid_forget()
            
        if name == "debate": self.tab_debate.grid(row=0, column=0, sticky="nsew")
        else: self.tab_debate.grid_forget()
            
        if name == "settings": self.tab_settings.grid(row=0, column=0, sticky="nsew")
        else: self.tab_settings.grid_forget()

    def show_dashboard(self): self.select_frame_by_name("dash")
    def show_debate(self): self.select_frame_by_name("debate")
    def show_settings(self): self.select_frame_by_name("settings")

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

        ctk.CTkLabel(frame, text="Deploy Mode", font=("Arial", 16, "bold")).pack(anchor="w", pady=(20,5))
        self.deploy_var = ctk.StringVar(value=CFG.DEPLOY_MODE)
        ctk.CTkRadioButton(frame, text="Auto Generate & Deploy", variable=self.deploy_var, value="auto").pack(anchor="w", pady=5)
        ctk.CTkRadioButton(frame, text="Recheck & Edit before Deploy", variable=self.deploy_var, value="manual").pack(anchor="w", pady=5)

        ctk.CTkButton(frame, text="💾 Save to .env", command=self.save_settings, fg_color=self.C_GREEN, hover_color="#00C853", text_color="black", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=30)

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
        content = update_or_add("DEPLOY_MODE", self.deploy_var.get(), content)

        env_path.write_text(content)
        
        CFG.NVIDIA_API_KEY = self.nv_api_var.get()
        CFG.GEMINI_API_KEY = self.gem_api_var.get()
        CFG.GENERATION_MODE = self.mode_var.get()
        CFG.VIDEO_TYPE_FILTER = self.filter_var.get()
        CFG.FORCE_REWATCH = self.rewatch_var.get()
        CFG.DEPLOY_MODE = self.deploy_var.get()
        
        self.log_debate("Settings saved successfully!")

    def build_dashboard_tab(self):
        # Top bar
        top_bar = ctk.CTkFrame(self.tab_dash, fg_color="transparent")
        top_bar.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkButton(top_bar, text="🔄 Fetch Videos", command=self.fetch_videos_thread, font=ctk.CTkFont(weight="bold"), fg_color="#2A2D3A", hover_color="#3A3D4A").pack(side="left", padx=(0, 10))
        self.btn_select_all = ctk.CTkButton(top_bar, text="☑ Select All", command=self.toggle_select_all, state="disabled", fg_color="gray", width=100)
        self.btn_select_all.pack(side="left", padx=10)
        self.btn_start = ctk.CTkButton(top_bar, text="▶ Start Processing", command=self.start_processing, fg_color=self.C_GREEN, hover_color="#00C853", text_color="black", text_color_disabled="gray30", font=ctk.CTkFont(weight="bold"), state="disabled")
        self.btn_start.pack(side="left", padx=10)
        self.btn_stop = ctk.CTkButton(top_bar, text="⏹ Stop", command=self.stop_processing, fg_color=self.C_RED, hover_color="#D50000", text_color="white", text_color_disabled="gray90", font=ctk.CTkFont(weight="bold"), state="disabled")
        self.btn_stop.pack(side="left", padx=10)
        
        # Fake press effect helper
        def add_press_effect(btn):
            orig_color = btn.cget("fg_color")
            def on_press(e): btn.configure(fg_color="#000000")
            def on_release(e): btn.configure(fg_color=orig_color)
            btn.bind("<Button-1>", on_press)
            btn.bind("<ButtonRelease-1>", on_release)
            
        add_press_effect(self.btn_start)
        add_press_effect(self.btn_stop)
        
        self.lbl_status = ctk.CTkLabel(top_bar, text="Status: Idle", font=ctk.CTkFont(size=13, slant="italic"), text_color=self.C_ACCENT)
        self.lbl_status.pack(side="right", padx=10)

        # Stat Cards
        stats_frame = ctk.CTkFrame(self.tab_dash, fg_color="transparent")
        stats_frame.pack(fill="x", padx=10, pady=(0, 20))
        stats_frame.grid_columnconfigure((0,1,2), weight=1)
        
        def make_stat_card(parent, title, color, col):
            card = ctk.CTkFrame(parent, fg_color="#1A1C23", corner_radius=12, border_width=1, border_color="#2A2D3A")
            card.grid(row=0, column=col, sticky="ew", padx=10)
            lbl_title = ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=13, weight="bold"), text_color="gray70")
            lbl_title.pack(anchor="w", padx=15, pady=(15, 5))
            lbl_val = ctk.CTkLabel(card, text="0", font=ctk.CTkFont(size=28, weight="bold"), text_color=color)
            lbl_val.pack(anchor="w", padx=15, pady=(0, 15))
            return lbl_val
            
        self.stat_total = make_stat_card(stats_frame, "Total Videos", self.C_ACCENT, 0)
        self.stat_pending = make_stat_card(stats_frame, "Pending Review", "#FFD600", 1)
        self.stat_done = make_stat_card(stats_frame, "Fully Deployed", self.C_GREEN, 2)

        # Progress
        self.prog_bar = ctk.CTkProgressBar(self.tab_dash, progress_color=self.C_ACCENT, height=8)
        self.prog_bar.pack(fill="x", padx=20, pady=(0, 15))
        self.prog_bar.set(0)

        # Video List area
        self.scroll_frame = ctk.CTkScrollableFrame(self.tab_dash, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=0)

    def toggle_select_all(self):
        self.all_selected = not self.all_selected
        for var in self.selection_vars:
            var.set(self.all_selected)
        self.btn_select_all.configure(text="☑ Deselect All" if self.all_selected else "☑ Select All")

    def build_debate_tab(self):
        self.debate_log = ctk.CTkTextbox(self.tab_debate, state="normal", wrap="word", font=("Consolas", 13), fg_color="#181A20", text_color="#E0E0E0")
        self.debate_log.pack(fill="both", expand=True, padx=20, pady=20)
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
            err_str = str(e)
            if "SSL" in err_str or "wrong version number" in err_str.lower():
                msg = (
                    "Fetch Error: Network blocked by Antivirus, Firewall, or Proxy!\n"
                    "Your computer's connection to YouTube is being intercepted. "
                    "This isn't a feature we built, it's Python failing to connect to the internet.\n"
                    "👉 Fix: Temporarily disable your VPN or Antivirus 'Web Shield', or check your proxy settings."
                )
            else:
                msg = f"Fetch Error: {err_str}"
            self.lbl_status.configure(text="Status: Fetch Failed (Network Issue)")
            self.log_debate(msg)

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

    def update_stats(self):
        total = len(self.videos)
        done = sum(1 for v in self.videos if progress.is_done(v.id))
        pending = total - done
        
        self.stat_total.configure(text=str(total))
        self.stat_done.configure(text=str(done))
        self.stat_pending.configure(text=str(pending))

    def update_listbox(self):
        # Clear existing
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
            
        self.selection_vars.clear()
        self.card_labels = {}

        for v in self.videos:
            var = ctk.BooleanVar(value=True)
            self.selection_vars.append(var)
            
            card = ctk.CTkFrame(self.scroll_frame, fg_color=self.C_CARD, corner_radius=12, border_width=1, border_color="#2A2D3A")
            card.pack(fill="x", padx=10, pady=8)
            
            def on_enter(e, c=card): c.configure(fg_color="#222530", border_color=self.C_ACCENT)
            def on_leave(e, c=card): c.configure(fg_color=self.C_CARD, border_color="#2A2D3A")
            card.bind("<Enter>", on_enter)
            card.bind("<Leave>", on_leave)
            
            top_row = ctk.CTkFrame(card, fg_color="transparent")
            top_row.pack(fill="x")
            
            cb = ctk.CTkCheckBox(top_row, text="", variable=var, width=30, fg_color=self.C_ACCENT, hover_color=self.C_HOVER)
            cb.pack(side="left", padx=15)
            
            # Fetch and display thumbnail
            thumb_img = self.get_thumbnail(v.id)
            if thumb_img:
                lbl_img = ctk.CTkLabel(top_row, text="", image=thumb_img)
                lbl_img.pack(side="left", padx=(0,15), pady=15)
                
            # Details frame
            details = ctk.CTkFrame(top_row, fg_color="transparent")
            details.pack(side="left", fill="both", expand=True, padx=(0,15), pady=15)
            
            lbl_title = ctk.CTkLabel(details, text=v.old_title, font=ctk.CTkFont(size=15, weight="bold"), anchor="w", text_color="gray95")
            lbl_title.pack(fill="x", pady=(0, 5))
            
            vtype = "Short" if v.duration_s <= CFG.MAX_DURATION_S else "Long"
            done_text = "✅ Processed" if progress.is_done(v.id) else "⏳ Pending"
            info_text = f"ID: {v.id}  •  {vtype}  •  {v.duration_s}s  •  {done_text}"
            
            lbl_info = ctk.CTkLabel(details, text=info_text, font=ctk.CTkFont(size=12), text_color="gray60", anchor="w")
            lbl_info.pack(fill="x")
            
            review_panel = ctk.CTkFrame(card, fg_color="#1E2029", corner_radius=10, border_width=1, border_color=self.C_ACCENT)
            # Not packed yet
            
            self.card_labels[v.id] = {
                "title": lbl_title,
                "info": lbl_info,
                "review_panel": review_panel,
                "card": card
            }
            
            def bind_hover(w):
                w.bind("<Enter>", on_enter)
                w.bind("<Leave>", on_leave)
                for child in w.winfo_children():
                    # Checkboxes and buttons have their own hover
                    if not isinstance(child, (ctk.CTkCheckBox, ctk.CTkButton, ctk.CTkTextbox)):
                        bind_hover(child)
            bind_hover(card)
            
        self.update_stats()

    def start_processing(self):
        if not self.videos:
            return
        self.is_running = True
        self.stop_requested = False
        
        self.prog_bar.configure(mode="indeterminate")
        self.prog_bar.start()
        
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
            
            ok = process_single_video(v, i, total, skip_done=CFG.SKIP_DONE, gui_callback=self.log_debate, review_callback=self.manual_review_callback)
            if ok:
                success_count += 1
                
            # Update the specific card visually
            if v.id in self.card_labels:
                lbl_dict = self.card_labels[v.id]
                lbl_title = lbl_dict["title"]
                lbl_info = lbl_dict["info"]
                display_title = v.new_title if getattr(v, "new_title", "") else v.old_title
                lbl_title.configure(text=display_title)
                if progress.is_done(v.id):
                    current_info = lbl_info.cget("text")
                    lbl_info.configure(text=current_info.replace("⏳ Pending", "✅ Processed"))
                    
            self.update_stats()
            
            if i < total and not self.stop_requested and not (CFG.SKIP_DONE and progress.is_done(v.id)):
                self.log_debate(f"  [Waiting {CFG.INTER_VIDEO_S}s for rate limits...]")
                time.sleep(CFG.INTER_VIDEO_S)
                
        self.prog_bar.stop()
        self.prog_bar.configure(mode="determinate")
        self.prog_bar.set(1.0)
        
        self.is_running = False
        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        self.lbl_status.configure(text=f"Status: Finished. ({success_count}/{total} successful)")

    def manual_review_callback(self, video_meta):
        # Called from background thread, just hand off to UI and immediately return
        self.after(0, self.expand_card_for_review, video_meta)

    def expand_card_for_review(self, video_meta):
        if video_meta.id not in self.card_labels:
            return
            
        lbl_dict = self.card_labels[video_meta.id]
        review_panel = lbl_dict["review_panel"]
        review_panel.pack(fill="x", padx=10, pady=(0,10))
        
        # Clear existing
        for widget in review_panel.winfo_children():
            widget.destroy()
            
        # Title
        ctk.CTkLabel(review_panel, text="Review & Edit AI Drafts", font=ctk.CTkFont(size=16, weight="bold"), text_color="white").pack(pady=(15,5))
        
        # SEO Badge
        score = video_meta.seo_score.get("total_score", 0) if getattr(video_meta, "seo_score", None) else 0
        score_color = self.C_GREEN if score >= 80 else ("#FFD600" if score >= 60 else self.C_RED)
        
        badge_frame = ctk.CTkFrame(review_panel, fg_color=score_color, corner_radius=20)
        badge_frame.pack(pady=(0, 10))
        ctk.CTkLabel(badge_frame, text=f"🌟 SEO Score: {score}/100", text_color="black", font=ctk.CTkFont(weight="bold")).pack(padx=15, pady=2)

        options = []
        if video_meta.draft_debate: options.append("Debate Final")
        if video_meta.draft_gemini: options.append("Gemini")
        if video_meta.draft_nvidia: options.append("NVIDIA")
            
        if not options: options.append("Current")
            
        title_var = ctk.StringVar()
        tags_var = ctk.StringVar()
        desc_box = ctk.CTkTextbox(review_panel, height=150)
        
        def load_draft(draft_name):
            d = {}
            if draft_name == "Debate Final": d = video_meta.draft_debate
            elif draft_name == "Gemini": d = video_meta.draft_gemini
            elif draft_name == "NVIDIA": d = video_meta.draft_nvidia
            
            title_var.set(d.get("title", video_meta.new_title) or video_meta.new_title)
            tags = d.get("tags", video_meta.new_tags) or video_meta.new_tags
            if isinstance(tags, list): tags = ", ".join(tags)
            tags_var.set(tags)
            
            desc_box.delete("1.0", "end")
            desc_box.insert("1.0", d.get("description", video_meta.new_desc) or video_meta.new_desc)

        if len(options) > 1:
            seg_btn = ctk.CTkSegmentedButton(review_panel, values=options, command=load_draft)
            seg_btn.pack(fill="x", padx=20, pady=(10, 5))
            seg_btn.set(options[0])
            
        load_draft(options[0])
        
        ctk.CTkLabel(review_panel, text="Title:", font=("Arial", 12, "bold")).pack(anchor="w", padx=20)
        ctk.CTkEntry(review_panel, textvariable=title_var).pack(fill="x", padx=20, pady=(0,10))
        
        ctk.CTkLabel(review_panel, text="Description:", font=("Arial", 12, "bold")).pack(anchor="w", padx=20)
        desc_box.pack(fill="x", padx=20, pady=(0,10))
        
        ctk.CTkLabel(review_panel, text="Tags (comma separated):", font=("Arial", 12, "bold")).pack(anchor="w", padx=20)
        ctk.CTkEntry(review_panel, textvariable=tags_var).pack(fill="x", padx=20, pady=(0,10))
        
        def on_approve():
            video_meta.new_title = title_var.get()
            video_meta.new_desc = desc_box.get("1.0", "end-1c")
            video_meta.new_tags = [t.strip() for t in tags_var.get().split(",") if t.strip()]
            
            review_panel.pack_forget()
            
            def deploy_task():
                try:
                    self.log_debate(f"Uploading {video_meta.id} to YouTube...")
                    get_youtube_client().update_video(video_meta)
                    progress.mark_done(video_meta.id)
                    
                    def update_ui():
                        lbl_title = lbl_dict["title"]
                        lbl_info = lbl_dict["info"]
                        lbl_title.configure(text=video_meta.new_title)
                        current_info = lbl_info.cget("text")
                        lbl_info.configure(text=current_info.replace("⏳ Pending", "✅ Processed"))
                        self.log_debate(f"✅ {video_meta.id} fully updated on YouTube!")
                        
                    self.after(0, update_ui)
                except Exception as e:
                    self.log_debate(f"❌ Failed to upload {video_meta.id}: {e}")
                    
            threading.Thread(target=deploy_task, daemon=True).start()
            
        def on_skip():
            review_panel.pack_forget()
            self.log_debate(f"⏭️ Skipped manual deployment for {video_meta.id}.")
            
        btn_frame = ctk.CTkFrame(review_panel, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(10,20))
        
        ctk.CTkButton(btn_frame, text="✅ Approve & Deploy", command=on_approve, fg_color=self.C_GREEN, hover_color="#00C853", text_color="black", font=ctk.CTkFont(weight="bold"), width=150).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="⏭️ Skip / Cancel", command=on_skip, fg_color=self.C_RED, hover_color="#D50000", font=ctk.CTkFont(weight="bold"), width=150).pack(side="right", padx=5)

def launch_gui():
    app = ZenMetaBotApp()
    app.mainloop()

if __name__ == "__main__":
    launch_gui()
