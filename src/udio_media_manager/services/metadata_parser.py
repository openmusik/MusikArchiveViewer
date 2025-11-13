"""
PROFESSIONAL-GRADE Udio Metadata Parser (Upgraded)
"""
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.exceptions import MetadataParseError
from ..utils.logging import get_logger

logger = get_logger(__name__)

class MetadataParser:
    """A comprehensive, single-pass parser for Udio .txt metadata files."""
    def __init__(self):
        self._key_value_pattern = re.compile(r'^\s*([^:]+?)\s*:\s*(.*)\s*$')
        self._section_pattern = re.compile(r'^\s*---\s*([A-Z\s]+)\s*---\s*$')
        # A comprehensive mapping of possible keys in the .txt file to our desired snake_case keys
        self._field_mappings = {
            'title': 'title', 'artist': 'artist', 'created': 'created_date',
            'duration': 'duration_str', 'plays': 'plays', 'likes': 'likes',
            'song id': 'song_id', 'generation id': 'generation_id', 'user id': 'user_id',
            'source url': 'source_url', 'audio url': 'audio_url', 'album art url': 'album_art_url',
            'video url': 'video_url', 'artist image url': 'artist_image_url',
            'finished': 'is_finished', 'publishable': 'is_publishable',
            'disliked': 'is_disliked', 'liked': 'is_liked',
            'parent id': 'parent_id', 'relationship type': 'relationship_type',
            'audio conditioning type': 'audio_conditioning_type',
            'capture method': 'capture_method', 'attribution': 'attribution',
        }

    def parse_txt_file(self, file_path: Path) -> Dict[str, Any]:
        """Parses a Udio metadata file and returns a structured dictionary."""
        try:
            content = file_path.read_text(encoding='utf-8', errors='replace')
            parsed_data = self._parse_content_statefully(content)
            # Add file-system metadata that isn't in the file content
            parsed_data['file_path'] = str(file_path.absolute())
            parsed_data['file_name'] = file_path.name
            return self._normalize_and_finalize(parsed_data)
        except Exception as e:
            raise MetadataParseError(f"Failed to parse {file_path}: {e}", file_path=file_path) from e

    def _parse_content_statefully(self, content: str) -> Dict[str, Any]:
        """Efficiently parses file content in a single pass using a state machine."""
        data: Dict[str, Any] = {}
        current_section: Optional[str] = None
        section_content: List[str] = []

        for line in content.splitlines():
            if section_match := self._section_pattern.match(line):
                if current_section: self._process_section(current_section, "\n".join(section_content).strip(), data)
                current_section = section_match.group(1).strip()
                section_content = []
            elif current_section:
                section_content.append(line)
            elif kv_match := self._key_value_pattern.match(line):
                key, value = kv_match.groups()
                norm_key = self._field_mappings.get(key.lower().strip())
                if norm_key:
                    data[norm_key] = value.strip()
                else:
                    data.setdefault('custom_fields', {})[key.strip()] = value.strip()
        
        if current_section: self._process_section(current_section, "\n".join(section_content).strip(), data)
        return data

    def _process_section(self, section_name: str, content: str, data: Dict[str, Any]):
        """Handles the content of a specific named section (e.g., --- LYRICS ---)."""
        section_key = section_name.lower().replace(' ', '_')
        data[section_key] = content

    def _normalize_and_finalize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Converts raw parsed data into correctly typed and structured fields."""
        final = {k: data.get(k) for k in self._field_mappings.values()}
        
        # Type conversions and defaults
        final['created_date'] = self._parse_date(data.get('created_date'))
        final['duration'] = self._parse_duration(data.get('duration_str'))
        final['plays'] = int(data.get('plays', 0))
        final['likes'] = int(data.get('likes', 0))
        
        # Boolean conversions
        for key in ['is_finished', 'is_publishable', 'is_disliked', 'is_liked']:
            final[key] = str(data.get(key, 'false')).lower() == 'true'

        # List conversions
        for key in ['tags', 'user_tags']:
             final[key] = [tag.strip() for tag in data.get(key, '').split(',') if tag.strip()]
        
        # Ensure section data exists, even if empty
        for section in ['prompt', 'lyrics', 'description', 'attribution']:
            final[section] = data.get(section, '')

        # Add file system info
        final['file_path'] = data.get('file_path', '')

        return final

    def _parse_duration(self, value: Optional[str]) -> float:
        """Parses various duration string formats into seconds."""
        if not value: return 0.0
        try:
            # UPGRADE: Use regex to find the first number, ignoring trailing text.
            match = re.search(r'[\d\.]+', value)
            if not match: return 0.0
            
            numeric_part = match.group(0)
            if ':' in numeric_part:
                parts = numeric_part.split(':')
                return (int(parts[0]) * 60) + float(parts[1])
            return float(numeric_part)
        except (ValueError, IndexError):
            logger.warning(f"Could not parse duration string: '{value}'")
            return 0.0

    def _parse_date(self, value: Optional[str]) -> Optional[datetime]:
        """Parses various date string formats into datetime objects."""
        if not value: return None
        # Common formats to try, from most to least specific
        formats = ['%Y-%m-%dT%H:%M:%S.%fZ', '%m/%d/%Y, %I:%M:%S %p', '%Y-%m-%d %H:%M:%S']
        for fmt in formats:
            try: return datetime.strptime(value.strip(), fmt)
            except ValueError: continue
        logger.warning(f"Could not parse date string: '{value}'")
        return None