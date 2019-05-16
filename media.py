import re
import requests
import json
import os
import PTN      # "parse_torrent_name" package


class Media(object):

    def __init__(self, file_path: str):
        """
        An object which represents some form of media file. Most of the data attributes are pretty self-
        explanatory.

        :param file_path: (string) an absolute path of the media file
        """
        self.path = file_path
        self.folder_name, self.file_name = os.path.split(self.path)
        self.title, self.extension = os.path.splitext(self.file_name)
        self.subtitles = False
        self.sub_path = ()
        self.sub_language = []
        self.id = None
        self.imdb_rating = 0
        self.year = ""

    def add_subs(self, sub_path: tuple):
        """
        Adds the passed folder as the subtitle path for this instance of the Media object.

        :param sub_path: (tuple) a tuple of absolute paths of the subtitle file/s
        """
        self.subtitles = True
        self.sub_path = sub_path

    def search_imdb_id(self) -> bool:
        """
        Searches through the OMDb API with the API key for a title and year. Returns a response
        which is transformed into text form (JSON)

        :return: (bool) Value if the response of the query was received.
        TODO: Make the requests an asynchronous operation.
        """
        media_type = "movie"
        url = "http://www.omdbapi.com/?apikey=678bc96c&t={0.title}&y={0.year}&type={1}".format(self, media_type)
        # Checks for internet connection
        response = requests.get(url)
        media_info = json.loads(response.text)

        try:
            self.id = int(media_info["imdbID"].replace("t", ""))
            self.title = media_info["Title"]
            self.year = media_info["Year"]
            self.imdb_rating = [item["Value"] for item in media_info["Ratings"] if item["Source"] ==
                                "Internet Movie Database"][0]
        except KeyError:
            # TODO: Consider adding a log of movies that were not found
            self.id = None
        finally:
            return media_info["Response"]

    def __str__(self) -> str:
        """
        String representation of the object instance.
        """
        return "ID: {0.id}\nName: {0.file_name}\nPath: {0.path}\nTitle: {0.title}\nFile type: {0.extension}" \
               "\nSubtitles: {0.subtitles}\nSubtitle language: {0.sub_language}\n\
               Subtitle location: {0.sub_path}\n\n".format(self)


class Movie(Media):

    def __init__(self, file_path: str):
        super().__init__(file_path=file_path)

    def add_subs(self, sub_path: tuple):
        super().add_subs(sub_path=sub_path)

    def extract_movie_info(self):
        """
        If package PTN (parse torrent name) fails to detect a title and a year, a batch of homemade regular
        expressions are deployed to give it a try.
        """
        movie_info = PTN.parse(self.title)
        try:
            self.title = movie_info["title"]
            self.year = movie_info["year"]
        except KeyError:
            self._parse_movie_name()

    def _parse_movie_name(self):
        """
        Several regular expressions specifically targeted to find the titles of movies from
        irregularly written ones. re.search is used because we want to match the regular expression
        throughout the string, not just the beginning that re.match would do.

        The year_match checks for the year after the title of the movie. For now it works only
        on movies. Example of titles it works on:
            "The Killing of a Sacred Deer.2017.1080p.WEB-DL.H264.AC3-EVO[EtHD]"
            "12 Angry Men 1957 1080p BluRay x264 AAC - Ozlem"
            "Life.Is.Beautiful.1997.1080p.BluRay.x264.anoXmous"
        """
        movie_regex = re.compile(r"(.*?[.| ])(\(\d{4}\)|\d{4}|\[\d{4}\])?([.| ].*)")
        if movie_regex.search(self.title) is not None:
            try:
                self.year = movie_regex.search(self.title).group(2).strip()
            except AttributeError:
                self.year = ""
            finally:
                self.title = movie_regex.search(self.title).group(1).strip()
                additional_regex = re.compile(r"(.*)(\[.*\])")
                if additional_regex.search(self.title) is not None:
                    self.title = additional_regex.search(self.title).group(1)

    def search_imdb_id(self) -> None or str:
        return super().search_imdb_id()

    def __str__(self) -> str:
        """
        String representation of the object instance.
        """
        return "Title: {0.title}\nYear: {0.year}\nMovie IMDb ID: {0.id}\nFile name: {0.file_name}\n" \
               "Path: {0.path}\nFile type: {0.extension}\nSubtitles: {0.subtitles}\n" \
               "Subtitle language: {0.sub_language}\nSubtitle location: {0.sub_path}\n\n".format(self)
