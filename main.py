from dataclasses import dataclass, field
from typing import List, Dict, Optional
import traceback
import time
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from database import DatabaseManager


@dataclass
class MovieInfo:
    """Movie information data structure."""
    title: str
    genres: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        """Return string representation of movie information."""
        if not self.genres:
            return self.title
        return f"{self.title} [{', '.join(self.genres)}]"


class LetterboxdScraper:
    """A scraper for Letterboxd user watchlists."""

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
    }

    def __init__(self):
        """Initialize the scraper with session and database connection."""
        self.common_movies: List[MovieInfo] = []
        self.error_message: str = ""
        self.session = self._create_session()
        self.db = DatabaseManager()

    def _create_session(self) -> requests.Session:
        """Create an HTTP session with retry mechanism."""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def _check_user_profile(self, username: str) -> None:
        """Verify user profile existence."""
        profile_url = f'https://letterboxd.com/{username}/'
        response = self.session.get(profile_url, headers=self.HEADERS, timeout=10)
        if response.status_code != 200:
            raise ValueError(f"User profile not found: {username}")

    def _fetch_watchlist_page(self, url: str) -> BeautifulSoup:
        """Fetch and parse a single watchlist page."""
        response = self.session.get(url, headers=self.HEADERS, timeout=10)
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch watchlist page: {url}")
        return BeautifulSoup(response.text, 'html.parser')

    def _extract_movie_info(self, film_poster) -> Optional[MovieInfo]:
        """Extract movie information from film poster element."""
        try:
            film_title = film_poster.get('data-film-name')
            if not film_title:
                img = film_poster.find('img', class_='image')
                film_title = img['alt'] if img and 'alt' in img.attrs else None

            if film_title:
                return MovieInfo(title=film_title)
            return None
        except Exception as e:
            print(f"Error parsing movie poster: {str(e)}")
            return None

    def _parse_movie_page(self, soup: BeautifulSoup) -> List[MovieInfo]:
        """Parse movie information from page content."""
        movies = []
        try:
            film_grid = (
                    soup.find('ul', class_='poster-list') or
                    soup.find('ul', class_='films-grid') or
                    soup.find('div', class_='films-grid')
            )

            if not film_grid:
                all_posters = soup.find_all('div', class_='film-poster')
                for poster in all_posters:
                    movie = self._extract_movie_info(poster)
                    if movie:
                        movies.append(movie)
            else:
                for film_item in film_grid.find_all('li', class_='poster-container'):
                    film_poster = film_item.find('div', class_='film-poster')
                    if film_poster:
                        movie = self._extract_movie_info(film_poster)
                        if movie:
                            movies.append(movie)

        except Exception as e:
            print(f"Page parsing error: {str(e)}")
            traceback.print_exc()

        return movies

    def get_user_watchlist(self, username: str, username2: str, progress_callback=None) -> List[MovieInfo]:
        """Retrieve user's watchlist with progress updates."""
        try:
            self._check_user_profile(username)

            watchlist_url = f'https://letterboxd.com/{username}/watchlist/'
            initial_page = self._fetch_watchlist_page(watchlist_url)

            # Determine total pages
            pagination = initial_page.find('div', class_='pagination')
            last_page = max(
                (int(a.text) for a in pagination.find_all('a') if a.text.isdigit()),
                default=1
            ) if pagination else 1

            user_watchlist = []
            for page_num in range(last_page):
                if progress_callback:
                    progress = (page_num + 1) / last_page * 100
                    progress_callback(progress, username)

                page_url = f'{watchlist_url}page/{page_num + 1}/'
                page_soup = self._fetch_watchlist_page(page_url)
                page_movies = self._parse_movie_page(page_soup)
                user_watchlist.extend(page_movies)

                time.sleep(1)  # Rate limiting

            if not user_watchlist:
                raise ValueError(f"No movies found for user: {username}")

            self._update_database(username, username2, user_watchlist)
            return user_watchlist

        except Exception as e:
            self.error_message = f"Failed to fetch watchlist ({username}): {str(e)}\n{traceback.format_exc()}"
            print(self.error_message)
            return []

    def _update_database(self, username: str, username2: str, movies: List[MovieInfo]) -> None:
        """Update database with user and movie information."""
        if not self.db.get_user(username):
            self.db.add_user(username)

        for movie in movies:
            movie_data = {'title': movie.title}
            self.db.add_user_movie(username, username2, movie_data)

        self.db.update_user_sync_time(username)

    def compare_watchlists(self, username1: str, username2: str, progress_callback=None) -> Dict:
        """Compare watchlists of two users."""
        try:
            user1_watchlist = self.get_user_watchlist(username1, username2, progress_callback)
            if not user1_watchlist:
                raise ValueError(f"Could not fetch watchlist for {username1}")

            user2_watchlist = self.get_user_watchlist(username2, username1, progress_callback)
            if not user2_watchlist:
                raise ValueError(f"Could not fetch watchlist for {username2}")

            common_titles = set(movie.title for movie in user1_watchlist) & \
                            set(movie.title for movie in user2_watchlist)

            self.common_movies = [
                movie for movie in user1_watchlist
                if movie.title in common_titles
            ]

            self.db.save_common_movies(username1, username2, self.common_movies)

            return {
                'status': 'success',
                'common_movies': self.common_movies,
                'user1_total': len(user1_watchlist),
                'user2_total': len(user2_watchlist),
                'common_total': len(self.common_movies),
                'statistics': self._calculate_statistics(user1_watchlist, user2_watchlist)
            }

        except Exception:
            return {
                'status': 'error',
                'message': 'user_not_found',
                'common_movies': []
            }

    def _calculate_statistics(self, list1: List[MovieInfo], list2: List[MovieInfo]) -> Dict:
        """Calculate statistics between two lists."""
        return {
            'overlap_percentage': len(self.common_movies) / min(len(list1), len(list2)) * 100,
            'total_unique_movies': len(set(movie.title for movie in list1 + list2))
        }

    def get_error_message(self) -> str:
        """Return the last error message."""
        return self.error_message