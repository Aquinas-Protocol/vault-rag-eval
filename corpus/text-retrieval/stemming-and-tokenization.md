---
title: "Stemming and Tokenization"
type: concept
sources: []
related:
  - "[[inverted-index]]"
  - "[[vector-embeddings-ann]]"
created: 2026-01-15
last-updated: 2026-01-15
---

# Stemming and Tokenization

## Overview
Before text can be indexed or searched it must be chopped into units and cleaned up so that variant spellings of the same idea line up. Tokenization is the step that splits a stream of characters into individual words or tokens, and stemming is the step that strips word endings so that related forms collapse to a shared root. Together they decide what counts as a match.

## Key Points
- Tokenization breaks raw text into discrete units, handling spaces, punctuation, and edge cases like hyphens or contractions.
- Stemming reduces inflected words to a common stem so that plural, past-tense, and other variants are treated as one.
- Case folding and accent removal further normalize tokens so capitalization does not split a term.
- Aggressive stemming boosts recall but can over-merge unrelated words; light normalization preserves precision.
- A stored exact token and a stemmed token serve different goals: literal matching versus broad matching.
- The same pipeline must run at both index time and query time, or lookups will silently miss.

## Details
Tokenization sounds trivial but is full of judgment calls. A naive splitter on whitespace mishandles punctuation, compound words, and languages without spaces between words. Production pipelines apply rules or learned models to decide boundaries, then lowercase the output and optionally remove diacritics so that surface variants converge.

Stemming applies suffix-stripping rules to fold inflections together, while a more careful alternative called lemmatization uses a dictionary to map a word to its true base form. The choice is a precision-versus-recall tradeoff: heavier folding finds more documents but risks conflating distinct meanings. A common pipeline preserves both signals by emitting two streams from a routine named normalize_token_stream(), one keeping the literal token and one keeping the stemmed root, so that exact matches can be scored higher than loose ones.

Whatever normalization is chosen must be applied identically when building the [[inverted-index]] and when parsing a user's query; a mismatch means a query token never equals its indexed counterpart. These exact-and-stemmed tokens also feed dense pipelines, where the cleaned text becomes input to the models discussed in [[vector-embeddings-ann]].
