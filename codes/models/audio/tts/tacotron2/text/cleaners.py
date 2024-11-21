""" from https://github.com/keithito/tacotron """

'''
Cleaners are transformations that run over the input text at both training and eval time.

Cleaners can be selected by passing a comma-delimited list of cleaner names as the "cleaners"
hyperparameter. Some cleaners are English-specific. You'll typically want to use:
  1. "english_cleaners" for English text
  2. "transliteration_cleaners" for non-English text that can be transliterated to ASCII using
     the Unidecode library (https://pypi.python.org/pypi/Unidecode)
  3. "basic_cleaners" if you do not want to transliterate (in this case, you should also update
     the symbols in symbols.py to match your data).
'''

import re
from unidecode import unidecode
from .numbers import normalize_numbers
from german_transliterate.core import GermanTransliterate


# Regular expression matching whitespace:
_whitespace_re = re.compile(r'\s+')

# List of (regular expression, replacement) pairs for abbreviations:
# _abbreviations = [(re.compile('\\b%s\\.' % x[0], re.IGNORECASE), x[1]) for x in [
#   ('mrs', 'misess'),
#   ('mr', 'mister'),
#   ('dr', 'doctor'),
#   ('st', 'saint'),
#   ('co', 'company'),
#   ('jr', 'junior'),
#   ('maj', 'major'),
#   ('gen', 'general'),
#   ('drs', 'doctors'),
#   ('rev', 'reverend'),
#   ('lt', 'lieutenant'),
#   ('hon', 'honorable'),
#   ('sgt', 'sergeant'),
#   ('capt', 'captain'),
#   ('esq', 'esquire'),
#   ('ltd', 'limited'),
#   ('col', 'colonel'),
#   ('ft', 'fort'),
# ]]

# List of (regular expression, replacement) pairs for Egyptian Arabic abbreviations:
_abbreviations = [(re.compile('\\b%s\\b' % x[0], re.IGNORECASE), x[1]) for x in [
    ('د', 'دكتور'),
    ('أ', 'أستاذ'),
    ('م', 'مهندس'),
    ('س', 'سيد'),
    ('سيدة', 'مدام'),
    ('ش', 'شيخ'),
    ('ب', 'باشا'),
]]

# Function to normalize Arabic text (e.g., remove diacritics, normalize specific letters):
def normalize_arabic(text):
    text = re.sub(r'[\u064B-\u0652]', '', text)  # Remove diacritics
    text = re.sub(r'[إأآا]', 'ا', text)          # Normalize alef variants to 'ا'
    text = re.sub(r'[ى]', 'ي', text)            # Normalize 'ى' to 'ي'
    text = re.sub(r'[ؤ]', 'و', text)            # Normalize 'ؤ' to 'و'
    text = re.sub(r'[ئ]', 'ي', text)            # Normalize 'ئ' to 'ي'
    return text


def expand_abbreviations(text):
  for regex, replacement in _abbreviations:
    text = re.sub(regex, replacement, text)
  return text

def expand_numbers(text):
    # Optionally normalize Arabic numerals (٠-٩) to Western numerals (0-9) or vice versa
    arabic_to_western = str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789')
    text = text.translate(arabic_to_western)  # Convert Arabic to Western numerals
    return text
# def expand_numbers(text):
#   return normalize_numbers(text)


def lowercase(text):
  return text.lower()


def collapse_whitespace(text):
  return re.sub(_whitespace_re, ' ', text)


def convert_to_ascii(text):
  return unidecode(text)


# def basic_cleaners(text):
#   '''Basic pipeline that lowercases and collapses whitespace without transliteration.'''
#   text = lowercase(text)
#   text = collapse_whitespace(text)
#   return text
def basic_cleaners(text):
    '''Basic pipeline that normalizes Arabic and collapses whitespace without transliteration.'''
    text = normalize_arabic(text)
    text = collapse_whitespace(text)
    return text


# def transliteration_cleaners(text):
#   '''Pipeline for non-English text that transliterates to ASCII.'''
#   text = convert_to_ascii(text)
#   text = lowercase(text)
#   text = collapse_whitespace(text)
#   return text
def transliteration_cleaners(text):
    '''Pipeline for non-English text that normalizes and optionally transliterates.'''
    text = normalize_arabic(text)
    text = collapse_whitespace(text)
    return text


# def english_cleaners(text):
#   '''Pipeline for English text, including number and abbreviation expansion.'''
#   text = GermanTransliterate().transliterate(text)
#   text = lowercase(text)
#   text = collapse_whitespace(text)
#   text = text.replace('"', '')
#   return text
def english_cleaners(text):
    '''Pipeline for Egyptian Arabic text, including abbreviation and number expansion.'''
    text = normalize_arabic(text)
    text = expand_abbreviations(text)
    text = expand_numbers(text)
    text = collapse_whitespace(text)
    return text
