/**
 * Advanced Filtering and Search Component
 * Provides comprehensive filtering, sorting, and search capabilities
 */

import React, { useState, useCallback, useMemo, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  IconButton,
  Button,
  Menu,
  Popover,
  Typography,
  Divider,
  Stack,
  Autocomplete,
  Slider,
  Switch,
  FormControlLabel,
  Collapse,
  Alert,
  Badge,
} from '@mui/material';
import {
  Search as SearchIcon,
  FilterList as FilterIcon,
  Clear as ClearIcon,
  Sort as SortIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Save as SaveIcon,
  Restore as RestoreIcon,
  Download as DownloadIcon,
} from '@mui/icons-material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';

export interface FilterOption {
  field: string;
  label: string;
  type: 'text' | 'select' | 'multiselect' | 'date' | 'daterange' | 'number' | 'range' | 'boolean';
  options?: { value: any; label: string }[];
  min?: number;
  max?: number;
  step?: number;
}

export interface SortOption {
  field: string;
  label: string;
  direction: 'asc' | 'desc';
}

export interface FilterValue {
  field: string;
  operator: 'equals' | 'contains' | 'startsWith' | 'endsWith' | 'gt' | 'gte' | 'lt' | 'lte' | 'between' | 'in' | 'notIn';
  value: any;
  label?: string;
}

export interface SearchConfig {
  fields: string[];
  placeholder?: string;
  caseSensitive?: boolean;
  exactMatch?: boolean;
}

export interface AdvancedFilteringProps {
  data: any[];
  filterOptions: FilterOption[];
  sortOptions: SortOption[];
  searchConfig?: SearchConfig;
  onFilteredDataChange?: (filteredData: any[], activeFilters: FilterValue[], searchTerm: string) => void;
  onSaveFilter?: (filterName: string, filters: FilterValue[], searchTerm: string) => void;
  onLoadFilter?: (filterName: string) => Promise<{ filters: FilterValue[]; searchTerm: string }>;
  savedFilters?: string[];
  enableExport?: boolean;
  maxResults?: number;
}

export const AdvancedFiltering: React.FC<AdvancedFilteringProps> = ({
  data,
  filterOptions,
  sortOptions,
  searchConfig,
  onFilteredDataChange,
  onSaveFilter,
  onLoadFilter,
  savedFilters = [],
  enableExport = true,
  maxResults = 1000,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [activeFilters, setActiveFilters] = useState<FilterValue[]>([]);
  const [sortBy, setSortBy] = useState<SortOption | null>(null);
  const [filterMenuAnchor, setFilterMenuAnchor] = useState<null | HTMLElement>(null);
  const [sortMenuAnchor, setSortMenuAnchor] = useState<null | HTMLElement>(null);
  const [expandedFilters, setExpandedFilters] = useState(false);
  const [saveFilterDialogOpen, setSaveFilterDialogOpen] = useState(false);
  const [filterName, setFilterName] = useState('');
  const [quickFilters, setQuickFilters] = useState<Record<string, any>>({});

  // Apply filters and search
  const filteredData = useMemo(() => {
    let result = [...data];

    // Apply search
    if (searchTerm && searchConfig) {
      const searchLower = searchConfig.caseSensitive ? searchTerm : searchTerm.toLowerCase();
      result = result.filter(item => {
        return searchConfig.fields.some(field => {
          const fieldValue = item[field];
          if (fieldValue == null) return false;
          
          const valueStr = searchConfig.caseSensitive 
            ? String(fieldValue) 
            : String(fieldValue).toLowerCase();
          
          if (searchConfig.exactMatch) {
            return valueStr === searchLower;
          } else {
            return valueStr.includes(searchLower);
          }
        });
      });
    }

    // Apply filters
    activeFilters.forEach(filter => {
      result = result.filter(item => {
        const fieldValue = item[filter.field];
        
        switch (filter.operator) {
          case 'equals':
            return fieldValue === filter.value;
          case 'contains':
            return String(fieldValue).toLowerCase().includes(String(filter.value).toLowerCase());
          case 'startsWith':
            return String(fieldValue).toLowerCase().startsWith(String(filter.value).toLowerCase());
          case 'endsWith':
            return String(fieldValue).toLowerCase().endsWith(String(filter.value).toLowerCase());
          case 'gt':
            return Number(fieldValue) > Number(filter.value);
          case 'gte':
            return Number(fieldValue) >= Number(filter.value);
          case 'lt':
            return Number(fieldValue) < Number(filter.value);
          case 'lte':
            return Number(fieldValue) <= Number(filter.value);
          case 'between':
            return Number(fieldValue) >= filter.value[0] && Number(fieldValue) <= filter.value[1];
          case 'in':
            return Array.isArray(filter.value) && filter.value.includes(fieldValue);
          case 'notIn':
            return Array.isArray(filter.value) && !filter.value.includes(fieldValue);
          default:
            return true;
        }
      });
    });

    // Apply sorting
    if (sortBy) {
      result.sort((a, b) => {
        const aValue = a[sortBy.field];
        const bValue = b[sortBy.field];
        
        let comparison = 0;
        if (aValue < bValue) comparison = -1;
        if (aValue > bValue) comparison = 1;
        
        return sortBy.direction === 'desc' ? -comparison : comparison;
      });
    }

    // Limit results
    if (result.length > maxResults) {
      result = result.slice(0, maxResults);
    }

    return result;
  }, [data, searchTerm, activeFilters, sortBy, searchConfig, maxResults]);

  // Notify parent of changes
  useEffect(() => {
    onFilteredDataChange?.(filteredData, activeFilters, searchTerm);
  }, [filteredData, activeFilters, searchTerm, onFilteredDataChange]);

  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(event.target.value);
  };

  const handleAddFilter = (filterOption: FilterOption, value: any, operator: FilterValue['operator'] = 'equals') => {
    const newFilter: FilterValue = {
      field: filterOption.field,
      operator,
      value,
      label: `${filterOption.label}: ${Array.isArray(value) ? value.join(', ') : value}`,
    };

    setActiveFilters(prev => {
      // Remove existing filter for the same field
      const filtered = prev.filter(f => f.field !== filterOption.field);
      return [...filtered, newFilter];
    });
    setFilterMenuAnchor(null);
  };

  const handleRemoveFilter = (field: string) => {
    setActiveFilters(prev => prev.filter(f => f.field !== field));
  };

  const handleClearAllFilters = () => {
    setActiveFilters([]);
    setSearchTerm('');
    setSortBy(null);
    setQuickFilters({});
  };

  const handleSortChange = (sortOption: SortOption) => {
    setSortBy(sortOption);
    setSortMenuAnchor(null);
  };

  const handleQuickFilterChange = (field: string, value: any) => {
    setQuickFilters(prev => ({ ...prev, [field]: value }));
    
    if (value !== null && value !== undefined && value !== '') {
      const filterOption = filterOptions.find(opt => opt.field === field);
      if (filterOption) {
        handleAddFilter(filterOption, value, 'equals');
      }
    } else {
      handleRemoveFilter(field);
    }
  };

  const handleSaveFilter = () => {
    if (filterName.trim()) {
      onSaveFilter?.(filterName.trim(), activeFilters, searchTerm);
      setSaveFilterDialogOpen(false);
      setFilterName('');
    }
  };

  const handleLoadFilter = async (savedFilterName: string) => {
    try {
      const { filters, searchTerm: savedSearchTerm } = await onLoadFilter?.(savedFilterName) || { filters: [], searchTerm: '' };
      setActiveFilters(filters);
      setSearchTerm(savedSearchTerm);
    } catch (error) {
      console.error('Error loading filter:', error);
    }
  };

  const renderFilterInput = (filterOption: FilterOption) => {
    const currentValue = quickFilters[filterOption.field] || '';

    switch (filterOption.type) {
      case 'text':
        return (
          <TextField
            label={filterOption.label}
            value={currentValue}
            onChange={(e) => handleQuickFilterChange(filterOption.field, e.target.value)}
            size="small"
            fullWidth
          />
        );

      case 'select':
        return (
          <FormControl size="small" fullWidth>
            <InputLabel>{filterOption.label}</InputLabel>
            <Select
              value={currentValue}
              label={filterOption.label}
              onChange={(e) => handleQuickFilterChange(filterOption.field, e.target.value)}
            >
              <MenuItem value="">All</MenuItem>
              {filterOption.options?.map(option => (
                <MenuItem key={option.value} value={option.value}>
                  {option.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        );

      case 'multiselect':
        return (
          <Autocomplete
            multiple
            options={filterOption.options || []}
            getOptionLabel={(option) => option.label}
            value={filterOption.options?.filter(opt => currentValue.includes?.(opt.value)) || []}
            onChange={(_, newValue) => {
              const values = newValue.map(item => item.value);
              handleQuickFilterChange(filterOption.field, values);
            }}
            renderInput={(params) => (
              <TextField
                {...params}
                label={filterOption.label}
                size="small"
              />
            )}
            renderTags={(value, getTagProps) =>
              value.map((option, index) => (
                <Chip
                  variant="outlined"
                  label={option.label}
                  size="small"
                  {...getTagProps({ index })}
                />
              ))
            }
          />
        );

      case 'number':
        return (
          <TextField
            label={filterOption.label}
            type="number"
            value={currentValue}
            onChange={(e) => handleQuickFilterChange(filterOption.field, Number(e.target.value))}
            size="small"
            fullWidth
            inputProps={{
              min: filterOption.min,
              max: filterOption.max,
              step: filterOption.step,
            }}
          />
        );

      case 'range':
        return (
          <Box>
            <Typography variant="body2" gutterBottom>
              {filterOption.label}
            </Typography>
            <Slider
              value={currentValue || [filterOption.min || 0, filterOption.max || 100]}
              onChange={(_, newValue) => handleQuickFilterChange(filterOption.field, newValue)}
              valueLabelDisplay="auto"
              min={filterOption.min || 0}
              max={filterOption.max || 100}
              step={filterOption.step || 1}
            />
          </Box>
        );

      case 'boolean':
        return (
          <FormControlLabel
            control={
              <Switch
                checked={currentValue || false}
                onChange={(e) => handleQuickFilterChange(filterOption.field, e.target.checked)}
              />
            }
            label={filterOption.label}
          />
        );

      case 'date':
        return (
          <LocalizationProvider dateAdapter={AdapterDateFns}>
            <DatePicker
              label={filterOption.label}
              value={currentValue || null}
              onChange={(newValue) => handleQuickFilterChange(filterOption.field, newValue)}
              slotProps={{
                textField: {
                  size: 'small',
                  fullWidth: true,
                },
              }}
            />
          </LocalizationProvider>
        );

      default:
        return null;
    }
  };

  const activeFilterCount = activeFilters.length + (searchTerm ? 1 : 0);

  return (
    <Card>
      <CardContent>
        {/* Search and Quick Actions */}
        <Box sx={{ display: 'flex', gap: 2, mb: 2, alignItems: 'center', flexWrap: 'wrap' }}>
          {/* Search */}
          {searchConfig && (
            <TextField
              placeholder={searchConfig.placeholder || 'Search...'}
              value={searchTerm}
              onChange={handleSearchChange}
              InputProps={{
                startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                endAdornment: searchTerm && (
                  <IconButton size="small" onClick={() => setSearchTerm('')}>
                    <ClearIcon />
                  </IconButton>
                ),
              }}
              size="small"
              sx={{ minWidth: 250 }}
            />
          )}

          {/* Filter Button */}
          <Badge badgeContent={activeFilterCount} color="primary">
            <Button
              startIcon={<FilterIcon />}
              onClick={(e) => setFilterMenuAnchor(e.currentTarget)}
              variant="outlined"
              size="small"
            >
              Filters
            </Button>
          </Badge>

          {/* Sort Button */}
          <Button
            startIcon={<SortIcon />}
            onClick={(e) => setSortMenuAnchor(e.currentTarget)}
            variant="outlined"
            size="small"
          >
            Sort {sortBy && `(${sortBy.label})`}
          </Button>

          {/* Clear All */}
          {activeFilterCount > 0 && (
            <Button
              startIcon={<ClearIcon />}
              onClick={handleClearAllFilters}
              size="small"
              color="error"
            >
              Clear All
            </Button>
          )}

          {/* Save Filter */}
          {onSaveFilter && activeFilterCount > 0 && (
            <Button
              startIcon={<SaveIcon />}
              onClick={() => setSaveFilterDialogOpen(true)}
              size="small"
              variant="outlined"
            >
              Save Filter
            </Button>
          )}

          {/* Expand/Collapse Quick Filters */}
          <Button
            startIcon={expandedFilters ? <ExpandLessIcon /> : <ExpandMoreIcon />}
            onClick={() => setExpandedFilters(!expandedFilters)}
            size="small"
          >
            Quick Filters
          </Button>
        </Box>

        {/* Active Filters Display */}
        {activeFilters.length > 0 && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" color="textSecondary" gutterBottom>
              Active Filters:
            </Typography>
            <Stack direction="row" spacing={1} flexWrap="wrap">
              {activeFilters.map((filter) => (
                <Chip
                  key={filter.field}
                  label={filter.label}
                  onDelete={() => handleRemoveFilter(filter.field)}
                  size="small"
                  color="primary"
                  variant="outlined"
                />
              ))}
            </Stack>
          </Box>
        )}

        {/* Quick Filters */}
        <Collapse in={expandedFilters}>
          <Box sx={{ mb: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
            <Typography variant="subtitle2" gutterBottom>
              Quick Filters
            </Typography>
            <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 2 }}>
              {filterOptions.slice(0, 6).map((filterOption) => (
                <Box key={filterOption.field}>
                  {renderFilterInput(filterOption)}
                </Box>
              ))}
            </Box>
          </Box>
        </Collapse>

        {/* Results Summary */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="body2" color="textSecondary">
            Showing {filteredData.length} of {data.length} results
            {filteredData.length >= maxResults && ` (limited to ${maxResults})`}
          </Typography>
          
          {enableExport && filteredData.length > 0 && (
            <Button
              startIcon={<DownloadIcon />}
              size="small"
              onClick={() => console.log('Export filtered data:', filteredData)}
            >
              Export Results
            </Button>
          )}
        </Box>

        {/* Performance Warning */}
        {filteredData.length >= maxResults && (
          <Alert severity="warning" sx={{ mt: 2 }}>
            Results limited to {maxResults} items for performance. Consider adding more specific filters.
          </Alert>
        )}
      </CardContent>

      {/* Filter Menu */}
      <Menu
        anchorEl={filterMenuAnchor}
        open={Boolean(filterMenuAnchor)}
        onClose={() => setFilterMenuAnchor(null)}
        PaperProps={{ sx: { maxWidth: 300, maxHeight: 400 } }}
      >
        {filterOptions.map((filterOption) => (
          <MenuItem
            key={filterOption.field}
            onClick={() => {
              // For simple filters, just toggle
              const hasFilter = activeFilters.some(f => f.field === filterOption.field);
              if (hasFilter) {
                handleRemoveFilter(filterOption.field);
              } else {
                // Show a simple input for the filter
                console.log('Add filter for:', filterOption.field);
              }
            }}
          >
            <Box>
              <Typography variant="body2">{filterOption.label}</Typography>
              <Typography variant="caption" color="textSecondary">
                {filterOption.type}
              </Typography>
            </Box>
          </MenuItem>
        ))}
        
        <Divider />
        
        {savedFilters.length > 0 && (
          <>
            <Typography variant="body2" sx={{ px: 2, py: 1, fontWeight: 'bold' }}>
              Saved Filters
            </Typography>
            {savedFilters.map((savedFilter) => (
              <MenuItem
                key={savedFilter}
                onClick={() => handleLoadFilter(savedFilter)}
              >
                <RestoreIcon sx={{ mr: 1 }} />
                {savedFilter}
              </MenuItem>
            ))}
          </>
        )}
      </Menu>

      {/* Sort Menu */}
      <Menu
        anchorEl={sortMenuAnchor}
        open={Boolean(sortMenuAnchor)}
        onClose={() => setSortMenuAnchor(null)}
      >
        <MenuItem onClick={() => setSortBy(null)}>
          <Typography>No Sorting</Typography>
        </MenuItem>
        <Divider />
        {sortOptions.map((sortOption) => (
          <MenuItem
            key={`${sortOption.field}-${sortOption.direction}`}
            onClick={() => handleSortChange(sortOption)}
            selected={sortBy?.field === sortOption.field && sortBy?.direction === sortOption.direction}
          >
            {sortOption.label} ({sortOption.direction === 'asc' ? 'A-Z' : 'Z-A'})
          </MenuItem>
        ))}
      </Menu>
    </Card>
  );
};

export default AdvancedFiltering;