/**
 * Export Functionality Component
 * Handles export of reports and charts in multiple formats (PDF, CSV, Excel)
 */

import React, { useState, useCallback } from 'react';
import {
  Box,
  Button,
  Menu,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  SelectChangeEvent,
  TextField,
  Checkbox,
  FormControlLabel,
  Typography,
  Alert,
  CircularProgress,
  Divider,
  Stack,
  Chip,
} from '@mui/material';
import {
  Download as DownloadIcon,
  PictureAsPdf as PdfIcon,
  TableChart as CsvIcon,
  Description as ExcelIcon,
  Image as ImageIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';
import { saveAs } from 'file-saver';
import * as XLSX from 'xlsx';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';

export interface ExportData {
  title: string;
  data: any[];
  chartElement?: HTMLElement | null;
  metadata?: {
    generatedBy?: string;
    generatedAt?: string;
    description?: string;
    filters?: Record<string, any>;
  };
}

export interface ExportOptions {
  format: 'pdf' | 'csv' | 'excel' | 'png' | 'jpg';
  includeCharts: boolean;
  includeMetadata: boolean;
  includeTimestamp: boolean;
  customFilename?: string;
  pageOrientation?: 'portrait' | 'landscape';
  chartQuality?: 'low' | 'medium' | 'high';
  dataRange?: 'all' | 'filtered' | 'selected';
}

export interface ExportFunctionalityProps {
  data: ExportData;
  onExportStart?: (format: string) => void;
  onExportComplete?: (format: string, success: boolean) => void;
  onExportError?: (error: string) => void;
  disabled?: boolean;
  buttonVariant?: 'contained' | 'outlined' | 'text';
  buttonSize?: 'small' | 'medium' | 'large';
}

export const ExportFunctionality: React.FC<ExportFunctionalityProps> = ({
  data,
  onExportStart,
  onExportComplete,
  onExportError,
  disabled = false,
  buttonVariant = 'outlined',
  buttonSize = 'medium',
}) => {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [optionsDialogOpen, setOptionsDialogOpen] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [exportFormat, setExportFormat] = useState<ExportOptions['format']>('pdf');
  const [exportOptions, setExportOptions] = useState<ExportOptions>({
    format: 'pdf',
    includeCharts: true,
    includeMetadata: true,
    includeTimestamp: true,
    pageOrientation: 'portrait',
    chartQuality: 'high',
    dataRange: 'all',
  });

  const handleMenuClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleQuickExport = async (format: ExportOptions['format']) => {
    setExportFormat(format);
    const options = { ...exportOptions, format };
    await performExport(options);
    handleMenuClose();
  };

  const handleAdvancedExport = (format: ExportOptions['format']) => {
    setExportFormat(format);
    setExportOptions(prev => ({ ...prev, format }));
    setOptionsDialogOpen(true);
    handleMenuClose();
  };

  const handleOptionsChange = (field: keyof ExportOptions, value: any) => {
    setExportOptions(prev => ({ ...prev, [field]: value }));
  };

  const generateFilename = (format: string): string => {
    const timestamp = new Date().toISOString().split('T')[0];
    const baseFilename = exportOptions.customFilename || 
      data.title.toLowerCase().replace(/[^a-z0-9]/g, '_');
    
    if (exportOptions.includeTimestamp) {
      return `${baseFilename}_${timestamp}.${format}`;
    }
    return `${baseFilename}.${format}`;
  };

  const exportToPDF = async (options: ExportOptions): Promise<void> => {
    const pdf = new jsPDF({
      orientation: options.pageOrientation || 'portrait',
      unit: 'mm',
      format: 'a4',
    });

    let yPosition = 20;

    // Add title
    pdf.setFontSize(20);
    pdf.text(data.title, 20, yPosition);
    yPosition += 15;

    // Add metadata if requested
    if (options.includeMetadata && data.metadata) {
      pdf.setFontSize(12);
      if (data.metadata.description) {
        pdf.text(`Description: ${data.metadata.description}`, 20, yPosition);
        yPosition += 10;
      }
      if (data.metadata.generatedAt) {
        pdf.text(`Generated: ${new Date(data.metadata.generatedAt).toLocaleString()}`, 20, yPosition);
        yPosition += 10;
      }
      if (data.metadata.filters) {
        pdf.text('Filters Applied:', 20, yPosition);
        yPosition += 7;
        Object.entries(data.metadata.filters).forEach(([key, value]) => {
          pdf.text(`  ${key}: ${value}`, 25, yPosition);
          yPosition += 7;
        });
      }
      yPosition += 10;
    }

    // Add chart if requested and available
    if (options.includeCharts && data.chartElement) {
      try {
        const canvas = await html2canvas(data.chartElement, {
          scale: options.chartQuality === 'high' ? 2 : options.chartQuality === 'medium' ? 1.5 : 1,
          backgroundColor: '#ffffff',
        });
        
        const imgData = canvas.toDataURL('image/png');
        const imgWidth = 170; // A4 width minus margins
        const imgHeight = (canvas.height * imgWidth) / canvas.width;
        
        // Check if we need a new page
        if (yPosition + imgHeight > 280) {
          pdf.addPage();
          yPosition = 20;
        }
        
        pdf.addImage(imgData, 'PNG', 20, yPosition, imgWidth, imgHeight);
        yPosition += imgHeight + 10;
      } catch (error) {
        console.error('Error adding chart to PDF:', error);
      }
    }

    // Add data table
    if (data.data.length > 0) {
      // Check if we need a new page
      if (yPosition > 200) {
        pdf.addPage();
        yPosition = 20;
      }

      pdf.setFontSize(14);
      pdf.text('Data Table', 20, yPosition);
      yPosition += 10;

      // Simple table implementation
      const headers = Object.keys(data.data[0]);
      const cellWidth = 170 / headers.length;
      
      pdf.setFontSize(10);
      
      // Headers
      headers.forEach((header, index) => {
        pdf.text(header, 20 + (index * cellWidth), yPosition);
      });
      yPosition += 7;

      // Data rows (limit to prevent overflow)
      const maxRows = Math.min(data.data.length, 30);
      for (let i = 0; i < maxRows; i++) {
        const row = data.data[i];
        headers.forEach((header, index) => {
          const value = String(row[header] || '').substring(0, 15); // Truncate long values
          pdf.text(value, 20 + (index * cellWidth), yPosition);
        });
        yPosition += 7;
        
        // Check if we need a new page
        if (yPosition > 280) {
          pdf.addPage();
          yPosition = 20;
        }
      }

      if (data.data.length > maxRows) {
        pdf.text(`... and ${data.data.length - maxRows} more rows`, 20, yPosition);
      }
    }

    // Save the PDF
    pdf.save(generateFilename('pdf'));
  };

  const exportToCSV = async (options: ExportOptions): Promise<void> => {
    if (data.data.length === 0) {
      throw new Error('No financial risk data to export');
    }

    let csvContent = '';
    
    // Add metadata as comments if requested
    if (options.includeMetadata && data.metadata) {
      csvContent += `# ${data.title}\n`;
      if (data.metadata.description) {
        csvContent += `# Description: ${data.metadata.description}\n`;
      }
      if (data.metadata.generatedAt) {
        csvContent += `# Generated: ${new Date(data.metadata.generatedAt).toLocaleString()}\n`;
      }
      csvContent += '\n';
    }

    // Headers
    const headers = Object.keys(data.data[0]);
    csvContent += headers.join(',') + '\n';

    // Data rows
    data.data.forEach(row => {
      const values = headers.map(header => {
        const value = row[header];
        // Escape commas and quotes in CSV
        if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
          return `"${value.replace(/"/g, '""')}"`;
        }
        return value || '';
      });
      csvContent += values.join(',') + '\n';
    });

    // Create and download file
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    saveAs(blob, generateFilename('csv'));
  };

  const exportToExcel = async (options: ExportOptions): Promise<void> => {
    if (data.data.length === 0) {
      throw new Error('No financial risk data to export');
    }

    const workbook = XLSX.utils.book_new();
    
    // Create main data worksheet
    const worksheet = XLSX.utils.json_to_sheet(data.data);
    XLSX.utils.book_append_sheet(workbook, worksheet, 'Data');

    // Add metadata worksheet if requested
    if (options.includeMetadata && data.metadata) {
      const metadataArray = [
        ['Title', data.title],
        ['Generated At', data.metadata.generatedAt ? new Date(data.metadata.generatedAt).toLocaleString() : ''],
        ['Description', data.metadata.description || ''],
        ['Generated By', data.metadata.generatedBy || ''],
      ];

      if (data.metadata.filters) {
        metadataArray.push(['', '']); // Empty row
        metadataArray.push(['Filters Applied', '']);
        Object.entries(data.metadata.filters).forEach(([key, value]) => {
          metadataArray.push([key, String(value)]);
        });
      }

      const metadataWorksheet = XLSX.utils.aoa_to_sheet(metadataArray);
      XLSX.utils.book_append_sheet(workbook, metadataWorksheet, 'Metadata');
    }

    // Save the file
    XLSX.writeFile(workbook, generateFilename('xlsx'));
  };

  const exportToImage = async (format: 'png' | 'jpg', options: ExportOptions): Promise<void> => {
    if (!data.chartElement) {
      throw new Error('No chart element available for image export');
    }

    try {
      const canvas = await html2canvas(data.chartElement, {
        scale: options.chartQuality === 'high' ? 2 : options.chartQuality === 'medium' ? 1.5 : 1,
        backgroundColor: '#ffffff',
      });

      canvas.toBlob((blob) => {
        if (blob) {
          saveAs(blob, generateFilename(format));
        }
      }, `image/${format}`, format === 'jpg' ? 0.9 : 1.0);
    } catch (error) {
      throw new Error(`Failed to export chart as ${format.toUpperCase()}`);
    }
  };

  const performExport = async (options: ExportOptions): Promise<void> => {
    setExporting(true);
    onExportStart?.(options.format);

    try {
      switch (options.format) {
        case 'pdf':
          await exportToPDF(options);
          break;
        case 'csv':
          await exportToCSV(options);
          break;
        case 'excel':
          await exportToExcel(options);
          break;
        case 'png':
          await exportToImage('png', options);
          break;
        case 'jpg':
          await exportToImage('jpg', options);
          break;
        default:
          throw new Error(`Unsupported export format: ${options.format}`);
      }

      onExportComplete?.(options.format, true);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Export failed';
      onExportError?.(errorMessage);
      onExportComplete?.(options.format, false);
    } finally {
      setExporting(false);
      setOptionsDialogOpen(false);
    }
  };

  const getFormatIcon = (format: string) => {
    switch (format) {
      case 'pdf':
        return <PdfIcon />;
      case 'csv':
        return <CsvIcon />;
      case 'excel':
        return <ExcelIcon />;
      case 'png':
      case 'jpg':
        return <ImageIcon />;
      default:
        return <DownloadIcon />;
    }
  };

  return (
    <>
      <Button
        variant={buttonVariant}
        size={buttonSize}
        startIcon={exporting ? <CircularProgress size={16} /> : <DownloadIcon />}
        onClick={handleMenuClick}
        disabled={disabled || exporting}
      >
        {exporting ? 'Exporting...' : 'Export'}
      </Button>

      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
        PaperProps={{
          sx: { minWidth: 200 }
        }}
      >
        <MenuItem onClick={() => handleQuickExport('pdf')}>
          <PdfIcon sx={{ mr: 1 }} />
          Export as PDF
        </MenuItem>
        <MenuItem onClick={() => handleQuickExport('csv')}>
          <CsvIcon sx={{ mr: 1 }} />
          Export as CSV
        </MenuItem>
        <MenuItem onClick={() => handleQuickExport('excel')}>
          <ExcelIcon sx={{ mr: 1 }} />
          Export as Excel
        </MenuItem>
        {data.chartElement && (
          <>
            <MenuItem onClick={() => handleQuickExport('png')}>
              <ImageIcon sx={{ mr: 1 }} />
              Export as PNG
            </MenuItem>
            <MenuItem onClick={() => handleQuickExport('jpg')}>
              <ImageIcon sx={{ mr: 1 }} />
              Export as JPG
            </MenuItem>
          </>
        )}
        <Divider />
        <MenuItem onClick={() => handleAdvancedExport('pdf')}>
          <SettingsIcon sx={{ mr: 1 }} />
          Advanced Options...
        </MenuItem>
      </Menu>

      {/* Advanced Export Options Dialog */}
      <Dialog
        open={optionsDialogOpen}
        onClose={() => setOptionsDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          Export Options - {exportFormat.toUpperCase()}
        </DialogTitle>
        <DialogContent>
          <Stack spacing={3} sx={{ mt: 1 }}>
            {/* Filename */}
            <TextField
              label="Custom Filename"
              value={exportOptions.customFilename || ''}
              onChange={(e) => handleOptionsChange('customFilename', e.target.value)}
              placeholder={data.title.toLowerCase().replace(/[^a-z0-9]/g, '_')}
              fullWidth
              helperText="Leave empty to use default filename"
            />

            {/* Include Options */}
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Include in Export
              </Typography>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={exportOptions.includeTimestamp}
                    onChange={(e) => handleOptionsChange('includeTimestamp', e.target.checked)}
                  />
                }
                label="Include timestamp in filename"
              />
              <FormControlLabel
                control={
                  <Checkbox
                    checked={exportOptions.includeMetadata}
                    onChange={(e) => handleOptionsChange('includeMetadata', e.target.checked)}
                  />
                }
                label="Include metadata and filters"
              />
              {data.chartElement && (
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={exportOptions.includeCharts}
                      onChange={(e) => handleOptionsChange('includeCharts', e.target.checked)}
                    />
                  }
                  label="Include charts and visualizations"
                />
              )}
            </Box>

            {/* PDF-specific options */}
            {exportFormat === 'pdf' && (
              <FormControl fullWidth>
                <InputLabel>Page Orientation</InputLabel>
                <Select
                  value={exportOptions.pageOrientation}
                  label="Page Orientation"
                  onChange={(e) => handleOptionsChange('pageOrientation', e.target.value)}
                >
                  <MenuItem value="portrait">Portrait</MenuItem>
                  <MenuItem value="landscape">Landscape</MenuItem>
                </Select>
              </FormControl>
            )}

            {/* Chart quality options */}
            {(exportFormat === 'png' || exportFormat === 'jpg' || (exportFormat === 'pdf' && exportOptions.includeCharts)) && (
              <FormControl fullWidth>
                <InputLabel>Chart Quality</InputLabel>
                <Select
                  value={exportOptions.chartQuality}
                  label="Chart Quality"
                  onChange={(e) => handleOptionsChange('chartQuality', e.target.value)}
                >
                  <MenuItem value="low">Low (Faster)</MenuItem>
                  <MenuItem value="medium">Medium</MenuItem>
                  <MenuItem value="high">High (Better Quality)</MenuItem>
                </Select>
              </FormControl>
            )}

            {/* Data range options */}
            <FormControl fullWidth>
              <InputLabel>Data Range</InputLabel>
              <Select
                value={exportOptions.dataRange}
                label="Data Range"
                onChange={(e) => handleOptionsChange('dataRange', e.target.value)}
              >
                <MenuItem value="all">All Data</MenuItem>
                <MenuItem value="filtered">Filtered Data Only</MenuItem>
                <MenuItem value="selected">Selected Data Only</MenuItem>
              </Select>
            </FormControl>

            {/* Preview */}
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Preview
              </Typography>
              <Stack direction="row" spacing={1} flexWrap="wrap">
                <Chip
                  icon={getFormatIcon(exportFormat)}
                  label={`Format: ${exportFormat.toUpperCase()}`}
                  size="small"
                />
                <Chip
                  label={`Filename: ${generateFilename(exportFormat)}`}
                  size="small"
                  variant="outlined"
                />
                <Chip
                  label={`${data.data.length} records`}
                  size="small"
                  variant="outlined"
                />
              </Stack>
            </Box>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOptionsDialogOpen(false)}>
            Cancel
          </Button>
          <Button
            onClick={() => performExport(exportOptions)}
            variant="contained"
            disabled={exporting}
            startIcon={exporting ? <CircularProgress size={16} /> : getFormatIcon(exportFormat)}
          >
            {exporting ? 'Exporting...' : 'Export'}
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default ExportFunctionality;