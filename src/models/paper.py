from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass
class Author:
    """Represents an author of an academic paper."""
    name: str
    author_id: Optional[str] = None
    url: Optional[str] = None


@dataclass
class Paper:
    """Represents an academic paper with metadata."""
    paper_id: str
    title: str
    abstract: Optional[str]
    authors: List[Author]
    year: Optional[int]
    citation_count: Optional[int]
    reference_count: Optional[int]
    url: Optional[str]
    venue: Optional[str] = None
    fields_of_study: List[str] = None
    publication_date: Optional[datetime] = None
    
    def __post_init__(self):
        if self.fields_of_study is None:
            self.fields_of_study = []
    
    def to_dict(self) -> dict:
        """Convert paper to dictionary for serialization."""
        return {
            "paper_id": self.paper_id,
            "title": self.title,
            "abstract": self.abstract,
            "authors": [{"name": author.name, "author_id": author.author_id, "url": author.url} 
                       for author in self.authors],
            "year": self.year,
            "citation_count": self.citation_count,
            "reference_count": self.reference_count,
            "url": self.url,
            "venue": self.venue,
            "fields_of_study": self.fields_of_study,
            "publication_date": self.publication_date.isoformat() if self.publication_date else None
        }
    
    @classmethod
    def from_semantic_scholar(cls, data: dict) -> 'Paper':
        """Create a Paper instance from Semantic Scholar API response."""
        authors = []
        for author_data in data.get("authors", []):
            authors.append(Author(
                name=author_data.get("name", ""),
                author_id=author_data.get("authorId"),
                url=author_data.get("url")
            ))
        
        # Parse publication date if available
        publication_date = None
        if data.get("publicationDate"):
            try:
                publication_date = datetime.fromisoformat(data["publicationDate"].replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                pass
        
        return cls(
            paper_id=data.get("paperId", ""),
            title=data.get("title", ""),
            abstract=data.get("abstract"),
            authors=authors,
            year=data.get("year"),
            citation_count=data.get("citationCount"),
            reference_count=data.get("referenceCount"),
            url=data.get("url"),
            venue=data.get("venue"),
            fields_of_study=data.get("fieldsOfStudy", []),
            publication_date=publication_date
        )


@dataclass
class SearchResult:
    """Represents the result of a paper search."""
    query: str
    papers: List[Paper]
    total_results: int
    search_time: float
    
    def to_dict(self) -> dict:
        """Convert search result to dictionary for serialization."""
        return {
            "query": self.query,
            "papers": [paper.to_dict() for paper in self.papers],
            "total_results": self.total_results,
            "search_time": self.search_time
        }