import React, { useState, useMemo, useRef, useEffect } from 'react';
import { LOCATIONS, Location } from '../data/locations';

interface LocationAutocompleteProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  onEnter?: () => void;
}

export function LocationAutocomplete({ value, onChange, placeholder = "City, State or Remote", onEnter }: LocationAutocompleteProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const wrapperRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Filter locations based on input
  const filteredLocations = useMemo(() => {
    if (!value) return LOCATIONS.slice(0, 50); // Show top 50 by default when empty
    
    const lowerValue = value.toLowerCase();
    return LOCATIONS.filter(loc => 
      loc.label.toLowerCase().includes(lowerValue)
    ).slice(0, 50); // Limit to top 50 matches for performance
  }, [value]);

  const handleSelect = (location: Location) => {
    onChange(location.label);
    setIsOpen(false);
    setHighlightedIndex(-1);
    // Remove focus from input if needed or trigger enter
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!isOpen) {
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
        setIsOpen(true);
      }
      return;
    }

    const maxIndex = filteredLocations.length === 0 && value.trim() !== '' ? 0 : filteredLocations.length - 1;
    
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setHighlightedIndex(prev => prev < maxIndex ? prev + 1 : prev);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setHighlightedIndex(prev => prev > 0 ? prev - 1 : 0);
    } else if (e.key === 'Enter') {
      if (highlightedIndex >= 0 && filteredLocations.length > 0) {
        e.preventDefault();
        handleSelect(filteredLocations[highlightedIndex]);
      } else if (filteredLocations.length === 0 && value.trim() !== '') {
        e.preventDefault();
        setIsOpen(false);
        if (onEnter) onEnter();
      }
    } else if (e.key === 'Escape') {
      setIsOpen(false);
    }
  };

  return (
    <div ref={wrapperRef} style={{ position: 'relative', flex: 1 }}>
      <input
        type="text"
        placeholder={placeholder}
        value={value}
        onChange={(e) => {
          onChange(e.target.value);
          setIsOpen(true);
          setHighlightedIndex(-1);
        }}
        onFocus={() => setIsOpen(true)}
        onKeyDown={(e) => {
          handleKeyDown(e);
          if (e.key === 'Enter' && highlightedIndex === -1 && onEnter && filteredLocations.length > 0) {
            onEnter();
            setIsOpen(false);
          }
        }}
        style={{ width: '100%', padding: '0.8rem', borderRadius: '8px', border: '1px solid var(--border-subtle)', background: 'rgba(0,0,0,0.3)', color: 'white', boxSizing: 'border-box' }}
      />
      
      {isOpen && filteredLocations.length > 0 && (
        <ul style={{
          position: 'absolute',
          top: '100%',
          left: 0,
          right: 0,
          maxHeight: '250px',
          overflowY: 'auto',
          background: 'var(--bg-secondary)',
          border: '1px solid var(--border)',
          borderRadius: '8px',
          marginTop: '4px',
          padding: '0',
          listStyle: 'none',
          zIndex: 1000,
          boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)'
        }}>
          {filteredLocations.map((loc, index) => (
            <li
              key={loc.id}
              onClick={() => handleSelect(loc)}
              onMouseEnter={() => setHighlightedIndex(index)}
              style={{
                padding: '0.75rem 1rem',
                cursor: 'pointer',
                background: index === highlightedIndex ? 'var(--bg-hover)' : 'transparent',
                color: 'var(--text-primary)',
                borderBottom: '1px solid var(--border)'
              }}
            >
              {loc.label}
            </li>
          ))}
          {filteredLocations.length === 0 && value.trim() !== '' && (
            <li
              onClick={() => {
                setIsOpen(false);
                if (onEnter) onEnter();
              }}
              onMouseEnter={() => setHighlightedIndex(0)}
              style={{
                padding: '0.75rem 1rem',
                cursor: 'pointer',
                background: highlightedIndex === 0 ? 'var(--bg-hover)' : 'transparent',
                color: 'var(--text-secondary)',
                borderBottom: '1px solid var(--border)',
                fontStyle: 'italic'
              }}
            >
              ⚠️ Search unverified location: "{value}"
            </li>
          )}
        </ul>
      )}
    </div>
  );
}
