INSERT INTO genre (genre_name, description) VALUES
    ('Rock', 'Rock and alternative rock'),
    ('Pop', 'Mainstream and contemporary pop'),
    ('Jazz', 'Jazz, fusion and related styles'),
    ('Classical', 'Classical and orchestral music'),
    ('Electronic', 'Electronic and dance music'),
    ('Hip-Hop', 'Hip-hop and rap'),
    ('R&B', 'Rhythm and blues'),
    ('Country', 'Country and Americana'),
    ('Metal', 'Heavy metal and related styles'),
    ('Indie', 'Independent and alternative music')
ON CONFLICT (genre_name) DO NOTHING;

INSERT INTO media_type (media_type_name, file_extension, mime_type) VALUES
    ('MP3', '.mp3', 'audio/mpeg'),
    ('FLAC', '.flac', 'audio/flac'),
    ('AAC', '.aac', 'audio/aac'),
    ('WAV', '.wav', 'audio/wav')
ON CONFLICT (media_type_name) DO NOTHING;
