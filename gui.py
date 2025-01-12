# GUI Libraries
import tkinter as tk
from collections.abc import Sized
from string import whitespace
from tkinter import messagebox
from tkinter import ttk

# Image Processing
from PIL import Image, ImageTk

# Project Modules
from main import LetterboxdScraper
from translations import TRANSLATIONS

# System Libraries
import threading
import os
import random
import webbrowser

# UI Constants
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
MIN_WINDOW_WIDTH = 600
MIN_WINDOW_HEIGHT = 400

# UI Colors and Styles
BUTTON_STYLE = {
    'padx': 20,
    'pady': 10,
    'bd': 0,
    'relief': 'flat',
    'activeforeground': 'black',
    'cursor': 'heart'
}

TEXT_COLOR = 'white'
ACCENT_COLOR = '#801919'


class FilmFusionApp:
    """
    FilmFusion GUI Application
    A movie comparison tool that helps users find common movies in their watchlists.
    """

    def __init__(self):
        """Initialize the FilmFusion application with default settings and UI components."""
        self.window = tk.Tk()
        self.window.title("FilmFusion")

        self.window.resizable(False, False)

        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()

        x = (screen_width - WINDOW_WIDTH) // 2
        y = (screen_height - WINDOW_HEIGHT) // 2

        self.window.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}")

        self.scraper = LetterboxdScraper()
        self.frames = {}
        self.current_language = 'tr'  # Default language
        self.translations = TRANSLATIONS

        # Application Settings
        self.settings = {
            'language': 'tr',
            'notifications': True,
            'auto_update': True,
            'cursor': 'heart'
        }

        self.load_background_image()
        self.create_frames()
        self.show_frame("HomePage")

    def get_text(self, key: str) -> str:

        return self.translations[self.current_language].get(key, key)

    def open_letterboxd_signup(self):
        """Open Letterboxd signup page in default browser."""
        webbrowser.open('https://www.letterboxd.com/signup')

    def load_background_image(self):
        """Load and prepare background images for the application."""
        # Load main background
        image_path = os.path.join(os.path.dirname(__file__), "images", "cinema_background.jpg")
        image = Image.open(image_path)
        image = image.resize((WINDOW_WIDTH, WINDOW_HEIGHT), Image.Resampling.LANCZOS)

        # Add overlay to main background
        overlay = Image.new('RGBA', image.size, (0, 0, 0, 128))
        image = Image.alpha_composite(image.convert('RGBA'), overlay)
        self.background_image = ImageTk.PhotoImage(image)

        # Load secondary background
        barbie_image_path = os.path.join(os.path.dirname(__file__), "images", "barbie.jpg")
        barbie_image = Image.open(barbie_image_path)
        barbie_image = barbie_image.resize((WINDOW_WIDTH, WINDOW_HEIGHT), Image.Resampling.LANCZOS)
        self.barbie_background_image = ImageTk.PhotoImage(barbie_image)

    def create_frames(self):
        """Create all application frames."""
        self._create_home_frame()
        self._create_login_frame()
        self._create_comparison_frame()
        self._create_random_movie_frame()
        self._create_details_frame()
        self._create_error_frame()
        self._create_about_frame()
        self._create_settings_frame()

    def _create_home_frame(self):
        """Create and configure the home page frame."""
        home_frame = tk.Frame(self.window)
        self.frames["HomePage"] = home_frame

        # Background setup
        bg_label = tk.Label(home_frame, image=self.background_image)
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        # Content container
        content_frame = tk.Frame(home_frame, bg="black")
        content_frame.place(relx=0.5, rely=0.3, anchor='center')

        # Title
        tk.Label(
            content_frame,
            text=self.get_text('app_title'),
            font=("Arial", 60, "bold"),
            fg=ACCENT_COLOR,
            background="black",

        ).pack(pady=20)

        # Navigation buttons
        for button_config in [
            ('start', lambda: self.show_frame("LoginPage")),
            ('about', lambda: self.show_frame("AboutPage")),
            ('settings', lambda: self.show_frame("SettingsPage"))
        ]:
            tk.Button(
                content_frame,
                text=self.get_text(button_config[0]),
                command=button_config[1],
                fg="#992920",
                font=("Arial", 16, "bold"),
                **BUTTON_STYLE
            ).pack(pady=10)

    def _create_login_frame(self):
        """Create and configure the login page frame."""
        login_frame = tk.Frame(self.window)
        self.frames["LoginPage"] = login_frame

        # Background
        bg_label = tk.Label(login_frame, image=self.barbie_background_image)
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        # Title
        tk.Label(
            login_frame,
            text=self.get_text('enter_usernames'),
            font=("Arial", 30, "bold"),
            fg="black",
            bg="#dadff2"

        ).pack(pady=20)

        # User input fields
        for user_num in [1, 2]:
            tk.Label(
                login_frame,
                text=self.get_text(f'user_{user_num}'),
                font=("Arial", 16, "bold"),
                fg="black",
                bg="#dadff2",
            ).pack(pady=5)

            entry = tk.Entry(login_frame, font=("Arial", 12))
            entry.pack(pady=5)
            entry.bind('<Return>', lambda e: self.compare_users())

            if user_num == 1:
                self.username1_entry = entry
            else:
                self.username2_entry = entry

        # Action buttons
        for button_config in [
            ('compare', self.compare_users),
            ('back', lambda: self.show_frame("HomePage"))
        ]:
            tk.Button(
                login_frame,
                text=self.get_text(button_config[0]),
                command=button_config[1],
                cursor="heart",
                fg="#992920",
                highlightbackground="#dadff2",
                font=("Arial", 16, "bold"),
            ).pack(pady=10)

    def _create_comparison_frame(self):
        """Create and configure the comparison page frame."""
        comparison_frame = tk.Frame(self.window)
        self.frames["ComparisonPage"] = comparison_frame

        # Title
        tk.Label(
            comparison_frame,
            text=self.get_text('common_movies'),
            font=("Arial", 30),
            fg="#de2618"
        ).pack(pady=20)

        # Movies list container
        listbox_frame = tk.Frame(comparison_frame)
        listbox_frame.pack(pady=10)

        # Scrollbar setup
        scrollbar = tk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Movies listbox
        self.movies_listbox = tk.Listbox(
            listbox_frame,
            width=70,
            height=25,
            yscrollcommand=scrollbar.set,
            fg="gray",
            selectmode='single',
            font=("Arial", 12, "bold"),
        )
        self.movies_listbox.pack(side=tk.LEFT)
        scrollbar.config(command=self.movies_listbox.yview)
        self.movies_listbox.bind('<<ListboxSelect>>', self.show_movie_details)

        # Action buttons
        for button_config in [
            ('pick_random_movie', self.select_random_movie),
            ('new_comparison', lambda: self.show_frame("LoginPage"))
        ]:
            tk.Button(
                comparison_frame,
                text=self.get_text(button_config[0]),
                command=button_config[1],
                bg='#e50914',
                cursor='heart',
                fg="black",
                font=("Arial", 12, "bold")
            ).pack(pady=10)

    def _create_random_movie_frame(self):
        """Create and configure the random movie selection frame."""
        random_movie_frame = tk.Frame(self.window)
        self.frames["RandomMoviePage"] = random_movie_frame

        # Title
        tk.Label(
            random_movie_frame,
            text=self.get_text('your_random_movie'),
            font=("Arial", 24, "bold"),
            fg="black"
        ).pack(pady=(50, 30))

        # Movie title container
        self.random_movie_title_frame = tk.Frame(
            random_movie_frame,
            bg='#e50914',
            padx=3,
            pady=3
        )
        self.random_movie_title_frame.pack(pady=20)

        # Movie title label
        self.random_movie_label = tk.Label(
            self.random_movie_title_frame,
            text="",
            font=("Arial", 18),
            bg="#801919",
            highlightbackground="#801919",
            fg="white",
            padx=20,
            pady=15
        )
        self.random_movie_label.pack()

        # Action buttons container
        buttons_frame = tk.Frame(random_movie_frame)
        buttons_frame.pack(pady=40)

        # Action buttons
        for button_config in [
            ('try_another', self.select_random_movie),
            ('back_to_movies', lambda: self.show_frame("ComparisonPage"))
        ]:
            tk.Button(
                buttons_frame,
                text=self.get_text(button_config[0]),
                command=button_config[1],
                bg='#e50914',
                fg="black",
                font=("Arial", 14, "bold"),
                padx=20,
                pady=10,
                cursor='heart',
                borderwidth=0,

            ).pack(pady=10)

    def _create_details_frame(self):
        """Create and configure the movie details frame."""
        details_frame = tk.Frame(self.window)
        self.frames["DetailsPage"] = details_frame

        # Movie details label
        self.details_label = tk.Label(
            details_frame,
            text=self.get_text('movie_details'),
            font=("Arial", 25, "bold"),
            fg="#de2618"
        )
        self.details_label.pack(pady=20)

        # Back button
        tk.Button(
            details_frame,
            text=self.get_text('back'),
            command=lambda: self.show_frame("ComparisonPage"),
            bg='#e50914',
            fg="black",
            cursor='heart',
            font=("Arial", 12, "bold")
        ).pack(pady=10)

    def _create_error_frame(self):
        """Create and configure the error page frame."""
        error_frame = tk.Frame(self.window)
        self.frames["ErrorPage"] = error_frame

        # Error message
        tk.Label(
            error_frame,
            text=self.get_text('error'),
            font=("Arial", 20),
            fg=TEXT_COLOR
        ).pack(pady=20)

        # Home button
        tk.Button(
            error_frame,
            text=self.get_text('home'),
            command=lambda: self.show_frame("HomePage"),
            bg='#e50914',
            fg=TEXT_COLOR,
            cursor='heart',
            font=("Arial", 12, "bold")
        ).pack(pady=10)

    def _create_about_frame(self):
        """Create and configure the about page frame."""
        about_frame = tk.Frame(self.window)
        self.frames["AboutPage"] = about_frame

        # Title
        tk.Label(
            about_frame,
            text=self.get_text('about_title'),
            font=("Arial", 24, "bold"),
            fg="#de2618"
        ).pack(pady=20)

        # Text container
        text_container = tk.Frame(about_frame)
        text_container.pack(fill=tk.BOTH, expand=True, padx=40, pady=20)

        # About text
        text_widget = tk.Text(
            text_container,
            wrap=tk.WORD,
            width=50,
            height=10,
            font=("Arial", 14),
            fg="grey",
            border=0,
            padx=20,
            pady=10,
            spacing1=8,
            spacing2=2,
            spacing3=8
        )
        text_widget.pack(fill=tk.BOTH, expand=True)

        # Insert content
        text_widget.insert('1.0', self.get_text('about_description') + '\n\n')

        # Configure link style
        text_widget.tag_configure(
            'link',
            foreground='blue',
            underline=True,
            font=("Arial", 14)
        )

        # Add signup text and link
        text_widget.insert('end', self.get_text('letterboxd_signup') + ' ', 'normal')
        text_widget.insert('end', 'letterboxd.com', 'link')
        text_widget.insert('end', ' ' + self.get_text('letterboxd_visit'), 'normal')

        # Link handler
        def open_letterboxd(event):
            """Open Letterboxd website when link is clicked."""
            webbrowser.open('https://letterboxd.com')

        # Bind link events
        text_widget.tag_bind('link', '<Button-1>', open_letterboxd)
        text_widget.tag_bind('link', '<Enter>', lambda e: text_widget.configure(cursor='hand2'))
        text_widget.tag_bind('link', '<Leave>', lambda e: text_widget.configure(cursor=''))

        # Disable text editing
        text_widget.configure(state='disabled')

        # Back button
        tk.Button(
            about_frame,
            text=self.get_text('back'),
            command=lambda: self.show_frame("HomePage"),
            bg='#e50914',
            fg="black",
            font=("Arial", 12, "bold"),
            cursor='heart',
        ).pack(pady=20)

    def _create_settings_frame(self):
        """Create and configure the settings page frame."""
        settings_frame = tk.Frame(self.window)
        self.frames["SettingsPage"] = settings_frame

        # Create notebook for settings tabs
        notebook = ttk.Notebook(settings_frame)
        notebook.pack(expand=True, fill="both", padx=10, pady=10)

        # General settings tab
        general_frame = tk.Frame(notebook)
        notebook.add(general_frame, text=self.get_text('general'))

        # Language settings
        languages = {
            'tr': 'Türkçe',
            'en': 'English'
        }

        self._create_setting_section(
            general_frame,
            self.get_text('language'),
            self.settings['language'],
            languages,
            callback=self.on_language_change
        )

        # Back button
        tk.Button(
            settings_frame,
            text=self.get_text('back'),
            command=lambda: self.show_frame("HomePage"),
            bg='#e50914',
            fg="black",
            font=("Arial", 12),
            padx=20,
            cursor='heart',
            pady=5
        ).pack(pady=10)

    def _create_setting_section(self, parent: tk.Frame, title: str,
                                current_value: str, options: dict, callback=None):
        # Create a container frame that will be centered
        frame = tk.Frame(parent)
        frame.pack(expand=True, fill='both', padx=20, pady=10)

        # Create an inner frame for the radio buttons
        radio_frame = tk.Frame(frame)
        radio_frame.place(relx=0.5, rely=0.5, anchor='center')  # Center in parent frame

        var = tk.StringVar(value=current_value)
        for key, value in options.items():
            radio = tk.Radiobutton(
                radio_frame,  # Changed parent to radio_frame
                text=value,
                variable=var,
                value=key,
                fg="#c21104",
                cursor='hand2',
                activeforeground=TEXT_COLOR,
                font=("Arial", 23),
                pady=5,
                padx=10
            )

            if callback:
                radio.config(command=lambda k=key: callback(k))
            else:
                radio.config(command=lambda k=key, t=title: self.update_setting(t.lower(), k))

            radio.pack(anchor='center', pady=5)  # Changed to center alignment

    def select_random_movie(self):
        """Select and display a random movie from the common movies list."""
        if hasattr(self, 'movies_listbox') and self.movies_listbox.size() > 0:
            movies = [self.movies_listbox.get(idx) for idx in range(self.movies_listbox.size())]
            random_movie = random.choice(movies)
            self.random_movie_label.config(text=str(random_movie))
            self.show_frame("RandomMoviePage")
        else:
            messagebox.showwarning(
                self.get_text('error'),
                self.get_text('error_no_movies')
            )

    def update_setting(self, setting: str, value: str):
        """
        Update application settings.

        Args:
            setting: Setting key to update
            value: New value for the setting
        """
        setting = setting.lower()
        if setting == self.get_text('language').lower():
            self.settings['language'] = value
            self.update_language()
        elif setting == self.get_text('date_format').lower():
            self.settings['date_format'] = value

    def compare_users(self):
        """Compare watchlists of two Letterboxd users."""
        username1 = self.username1_entry.get()
        username2 = self.username2_entry.get()

        # Input validation
        if not username1 or not username2:
            messagebox.showerror(
                self.get_text('error'),
                self.get_text('error_enter_both')
            )
            return

        # Show loading indicator
        loading_label = tk.Label(
            self.frames["LoginPage"],
            text=self.get_text('loading'),
            font=("Arial", 12),
            bg="#dadff2",
            fg="black",
        )
        loading_label.pack(pady=10)
        self.window.update()

        # Start comparison in background thread
        def comparison_thread():
            result = self.scraper.compare_watchlists(username1, username2)
            self.window.after(0, self.handle_comparison_result, result, loading_label)

        thread = threading.Thread(target=comparison_thread)
        thread.start()

    def handle_comparison_result(self, result: dict, loading_label: tk.Label):
        """
        Handle the result of watchlist comparison.

        Args:
            result: Dictionary containing comparison results
            loading_label: Loading indicator label to remove
        """
        loading_label.destroy()

        if result['status'] == 'success':
            self.movies_listbox.delete(0, tk.END)
            for movie in result['common_movies']:
                self.movies_listbox.insert(tk.END, str(movie))

            self.show_frame("ComparisonPage")
        else:
            error_message = self.get_text(result['message'])
            messagebox.showerror(self.get_text('error'), error_message)

    def show_movie_details(self, event):
        """Display details for the selected movie."""
        selection = self.movies_listbox.curselection()
        if selection:
            movie_name = self.movies_listbox.get(selection[0])
            self.show_frame("DetailsPage")
            self.details_label.config(
                text=f"{self.get_text('movie_details')}: {movie_name}"
            )

    def show_frame(self, frame_name: str):
        """
        Switch to the specified frame.

        Args:
            frame_name: Name of the frame to display
        """
        for frame in self.frames.values():
            frame.pack_forget()
        self.frames[frame_name].pack(fill="both", expand=True)
        self.window.update_idletasks()
        self.window.minsize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)

    def update_language(self):
        """Update all UI text elements when language changes."""
        self.current_language = self.settings['language']

        # Update main window title
        self.window.title(self.get_text('app_title'))

        # Update all frame contents
        self.update_home_page()
        self.update_login_page()
        self.update_comparison_page()
        self.update_random_movie_page()
        self.update_details_page()
        self.update_about_page()
        self.update_settings_page()

    def update_home_page(self):
        """Update text elements on the home page."""
        if "HomePage" not in self.frames:
            return

        home_frame = self.frames["HomePage"]
        for widget in home_frame.winfo_children():
            if isinstance(widget, tk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, tk.Button):
                        text = child.cget('text').lower()
                        if 'start' in text or 'başla' in text:
                            child.config(text=self.get_text('start'))
                        elif 'about' in text or 'hakkında' in text:
                            child.config(text=self.get_text('about'))
                        elif 'settings' in text or 'ayarlar' in text:
                            child.config(text=self.get_text('settings'))

    def update_login_page(self):
        """Update text elements on the login page."""
        if "LoginPage" not in self.frames:
            return

        login_frame = self.frames["LoginPage"]
        for widget in login_frame.winfo_children():
            if isinstance(widget, tk.Label):
                text = widget.cget('text').lower()
                if 'enter' in text or 'kullanıcı adlarını' in text:
                    widget.config(text=self.get_text('enter_usernames'))
                elif 'user 1' in text or 'kullanıcı 1' in text:
                    widget.config(text=self.get_text('user_1'))
                elif 'user 2' in text or 'kullanıcı 2' in text:
                    widget.config(text=self.get_text('user_2'))
            elif isinstance(widget, tk.Button):
                text = widget.cget('text').lower()
                if 'compare' in text or 'karşılaştır' in text:
                    widget.config(text=self.get_text('compare'))
                elif 'back' in text or 'geri' in text:
                    widget.config(text=self.get_text('back'))

    def update_comparison_page(self):
        """Update text elements on the comparison page."""
        if "ComparisonPage" not in self.frames:
            return

        comparison_frame = self.frames["ComparisonPage"]
        for widget in comparison_frame.winfo_children():
            if isinstance(widget, tk.Label):
                if 'common movies' in widget.cget('text').lower() or 'ortak filmler' in widget.cget('text').lower():
                    widget.config(text=self.get_text('common_movies'), fg="red")
            elif isinstance(widget, tk.Button):
                text = widget.cget('text').lower()
                if 'random' in text or 'rastgele' in text:
                    widget.config(text=self.get_text('pick_random_movie'))
                elif 'new comparison' in text or 'yeni karşılaştırma' in text:
                    widget.config(text=self.get_text('new_comparison'))

    def update_random_movie_page(self):
        """Update text elements on the random movie page."""
        if "RandomMoviePage" not in self.frames:
            return

        random_movie_frame = self.frames["RandomMoviePage"]
        for widget in random_movie_frame.winfo_children():
            if isinstance(widget, tk.Label) and not isinstance(widget, tk.Button):
                if 'your random movie' in widget.cget('text').lower() or 'rastgele seçilen film' in widget.cget(
                        'text').lower():
                    widget.config(text=self.get_text('your_random_movie'))
            elif isinstance(widget, tk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, tk.Button):
                        text = child.cget('text').lower()
                        if 'try another' in text or 'başka bir film' in text:
                            child.config(text=self.get_text('try_another'))
                        elif 'back to movie' in text or 'film listesine' in text:
                            child.config(text=self.get_text('back_to_movies'))

    def update_details_page(self):
        """Update text elements on the details page."""
        if "DetailsPage" not in self.frames:
            return

        details_frame = self.frames["DetailsPage"]
        for widget in details_frame.winfo_children():
            if isinstance(widget, tk.Label):
                if 'movie details' in widget.cget('text').lower() or 'film detayları' in widget.cget('text').lower():
                    widget.config(text=self.get_text('movie_details'))
            elif isinstance(widget, tk.Button):
                if 'back' in widget.cget('text').lower() or 'geri' in widget.cget('text').lower():
                    widget.config(text=self.get_text('back'))

    def update_about_page(self):
        """Update text elements on the about page."""
        if "AboutPage" not in self.frames:
            return

        about_frame = self.frames["AboutPage"]
        for widget in about_frame.winfo_children():
            if isinstance(widget, tk.Label):
                text = widget.cget('text').lower()
                if 'filmfusion' in text.lower():
                    widget.config(text=self.get_text('about_title'))
            elif isinstance(widget, tk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, tk.Text):
                        child.config(state='normal')
                        child.delete('1.0', tk.END)
                        child.insert('1.0', self.get_text('about_description') + '\n\n')
                        child.insert('end', self.get_text('letterboxd_signup') + ' ', 'normal')
                        child.insert('end', 'letterboxd.com', 'link')
                        child.insert('end', ' ' + self.get_text('letterboxd_visit'), 'normal')

                        child.config(state='disabled')
            elif isinstance(widget, tk.Button):
                if 'back' in widget.cget('text').lower() or 'geri' in widget.cget('text').lower():
                    widget.config(text=self.get_text('back'))

    def update_settings_page(self):
        """Update text elements on the settings page."""
        if "SettingsPage" not in self.frames:
            return
        settings_frame = self.frames["SettingsPage"]

        for widget in settings_frame.winfo_children():
            if isinstance(widget, ttk.Notebook):
                widget.tab(0, text=self.get_text('general'))
            elif isinstance(widget, tk.Button):
                if 'back' in widget.cget('text').lower() or 'geri' in widget.cget('text').lower():
                    widget.config(text=self.get_text('back'))

    def on_language_change(self, new_language: str):
        """
        Handle language change event.

        Args:
            new_language: New language code to switch to
        """
        self.current_language = new_language
        self.settings['language'] = new_language
        self.update_language()

    def run(self):
        """Start the application main loop."""
        self.window.mainloop()


def main():
    """
    Application entry point.
    Creates and runs the FilmFusion application.
    """
    app = FilmFusionApp()
    app.run()


if __name__ == "__main__":
    main()