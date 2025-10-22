/**
 * RiskIntel360 Design System - Grid System
 * Responsive grid system for consistent layouts
 */

import React, { forwardRef } from 'react';
import { Box, BoxProps } from '@mui/material';
import { styled } from '@mui/material/styles';
import { breakpoints, spacing } from '../../tokens';

// Grid container props
export interface GridContainerProps extends BoxProps {
  spacing?: number | string;
  rowSpacing?: number | string;
  columnSpacing?: number | string;
  columns?: number | { xs?: number; sm?: number; md?: number; lg?: number; xl?: number };
  alignItems?: 'flex-start' | 'center' | 'flex-end' | 'stretch' | 'baseline';
  justifyContent?: 'flex-start' | 'center' | 'flex-end' | 'space-between' | 'space-around' | 'space-evenly';
  direction?: 'row' | 'column' | 'row-reverse' | 'column-reverse';
  wrap?: 'nowrap' | 'wrap' | 'wrap-reverse';
}

// Grid item props
export interface GridItemProps extends BoxProps {
  xs?: number | 'auto';
  sm?: number | 'auto';
  md?: number | 'auto';
  lg?: number | 'auto';
  xl?: number | 'auto';
  offset?: number | { xs?: number; sm?: number; md?: number; lg?: number; xl?: number };
  order?: number | { xs?: number; sm?: number; md?: number; lg?: number; xl?: number };
}

// Styled grid container
const StyledGridContainer = styled(Box)<GridContainerProps>(
  ({ theme, spacing: gridSpacing, rowSpacing, columnSpacing, columns, alignItems, justifyContent, direction, wrap }) => {
    const gap = gridSpacing || spacing.scale[4]; // Default 16px
    const rowGap = rowSpacing || gap;
    const colGap = columnSpacing || gap;

    return {
      display: 'grid',
      gap: typeof gap === 'number' ? `${gap * 4}px` : gap,
      rowGap: typeof rowGap === 'number' ? `${rowGap * 4}px` : rowGap,
      columnGap: typeof colGap === 'number' ? `${colGap * 4}px` : colGap,
      alignItems,
      justifyContent,
      
      // Handle responsive columns
      ...(typeof columns === 'number' 
        ? { gridTemplateColumns: `repeat(${columns}, 1fr)` }
        : columns && {
            gridTemplateColumns: 'repeat(1, 1fr)', // Default
            [breakpoints.up.sm]: columns.sm && { gridTemplateColumns: `repeat(${columns.sm}, 1fr)` },
            [breakpoints.up.md]: columns.md && { gridTemplateColumns: `repeat(${columns.md}, 1fr)` },
            [breakpoints.up.lg]: columns.lg && { gridTemplateColumns: `repeat(${columns.lg}, 1fr)` },
            [breakpoints.up.xl]: columns.xl && { gridTemplateColumns: `repeat(${columns.xl}, 1fr)` },
          }
      ),
    };
  }
);

// Styled grid item
const StyledGridItem = styled(Box)<GridItemProps>(
  ({ theme, xs, sm, md, lg, xl, offset, order }) => {
    const styles: any = {};

    // Handle grid column spans
    if (xs) {
      styles.gridColumn = xs === 'auto' ? 'auto' : `span ${xs}`;
    }

    // Responsive column spans
    if (sm) {
      styles[breakpoints.up.sm] = {
        gridColumn: sm === 'auto' ? 'auto' : `span ${sm}`,
      };
    }
    if (md) {
      styles[breakpoints.up.md] = {
        ...styles[breakpoints.up.md],
        gridColumn: md === 'auto' ? 'auto' : `span ${md}`,
      };
    }
    if (lg) {
      styles[breakpoints.up.lg] = {
        ...styles[breakpoints.up.lg],
        gridColumn: lg === 'auto' ? 'auto' : `span ${lg}`,
      };
    }
    if (xl) {
      styles[breakpoints.up.xl] = {
        ...styles[breakpoints.up.xl],
        gridColumn: xl === 'auto' ? 'auto' : `span ${xl}`,
      };
    }

    // Handle offset
    if (offset) {
      if (typeof offset === 'number') {
        styles.marginLeft = `calc(${(offset / 12) * 100}% + ${offset * 8}px)`;
      } else {
        if (offset.xs) styles.marginLeft = `calc(${(offset.xs / 12) * 100}% + ${offset.xs * 8}px)`;
        if (offset.sm) {
          styles[breakpoints.up.sm] = {
            ...styles[breakpoints.up.sm],
            marginLeft: `calc(${(offset.sm / 12) * 100}% + ${offset.sm * 8}px)`,
          };
        }
        if (offset.md) {
          styles[breakpoints.up.md] = {
            ...styles[breakpoints.up.md],
            marginLeft: `calc(${(offset.md / 12) * 100}% + ${offset.md * 8}px)`,
          };
        }
        if (offset.lg) {
          styles[breakpoints.up.lg] = {
            ...styles[breakpoints.up.lg],
            marginLeft: `calc(${(offset.lg / 12) * 100}% + ${offset.lg * 8}px)`,
          };
        }
        if (offset.xl) {
          styles[breakpoints.up.xl] = {
            ...styles[breakpoints.up.xl],
            marginLeft: `calc(${(offset.xl / 12) * 100}% + ${offset.xl * 8}px)`,
          };
        }
      }
    }

    // Handle order
    if (order) {
      if (typeof order === 'number') {
        styles.order = order;
      } else {
        if (order.xs) styles.order = order.xs;
        if (order.sm) {
          styles[breakpoints.up.sm] = {
            ...styles[breakpoints.up.sm],
            order: order.sm,
          };
        }
        if (order.md) {
          styles[breakpoints.up.md] = {
            ...styles[breakpoints.up.md],
            order: order.md,
          };
        }
        if (order.lg) {
          styles[breakpoints.up.lg] = {
            ...styles[breakpoints.up.lg],
            order: order.lg,
          };
        }
        if (order.xl) {
          styles[breakpoints.up.xl] = {
            ...styles[breakpoints.up.xl],
            order: order.xl,
          };
        }
      }
    }

    return styles;
  }
);

// Grid container component
export const GridContainer = forwardRef<HTMLDivElement, GridContainerProps>(
  ({ children, ...props }, ref) => {
    return (
      <StyledGridContainer ref={ref} {...props}>
        {children}
      </StyledGridContainer>
    );
  }
);

GridContainer.displayName = 'GridContainer';

// Grid item component
export const GridItem = forwardRef<HTMLDivElement, GridItemProps>(
  ({ children, ...props }, ref) => {
    return (
      <StyledGridItem ref={ref} {...props}>
        {children}
      </StyledGridItem>
    );
  }
);

GridItem.displayName = 'GridItem';

// Flexbox-based grid for simpler layouts
export interface FlexGridProps extends BoxProps {
  spacing?: number;
  columns?: number | { xs?: number; sm?: number; md?: number; lg?: number; xl?: number };
  minItemWidth?: string;
  alignItems?: 'flex-start' | 'center' | 'flex-end' | 'stretch';
  justifyContent?: 'flex-start' | 'center' | 'flex-end' | 'space-between' | 'space-around';
}

const StyledFlexGrid = styled(Box)<FlexGridProps>(
  ({ theme, spacing: gridSpacing, columns, minItemWidth, alignItems, justifyContent }) => {
    const gap = gridSpacing ? `${gridSpacing * 4}px` : spacing.scale[4];

    let gridTemplateColumns = '1fr';
    
    if (minItemWidth) {
      gridTemplateColumns = `repeat(auto-fit, minmax(${minItemWidth}, 1fr))`;
    } else if (typeof columns === 'number') {
      gridTemplateColumns = `repeat(${columns}, 1fr)`;
    } else if (columns) {
      // Default to 1 column, then responsive
      gridTemplateColumns = 'repeat(1, 1fr)';
    }

    return {
      display: 'grid',
      gap,
      gridTemplateColumns,
      alignItems,
      justifyContent,
      
      // Responsive columns
      ...(typeof columns === 'object' && {
        [breakpoints.up.sm]: columns.sm && { gridTemplateColumns: `repeat(${columns.sm}, 1fr)` },
        [breakpoints.up.md]: columns.md && { gridTemplateColumns: `repeat(${columns.md}, 1fr)` },
        [breakpoints.up.lg]: columns.lg && { gridTemplateColumns: `repeat(${columns.lg}, 1fr)` },
        [breakpoints.up.xl]: columns.xl && { gridTemplateColumns: `repeat(${columns.xl}, 1fr)` },
      }),
    };
  }
);

export const FlexGrid = forwardRef<HTMLDivElement, FlexGridProps>(
  ({ children, ...props }, ref) => {
    return (
      <StyledFlexGrid ref={ref} {...props}>
        {children}
      </StyledFlexGrid>
    );
  }
);

FlexGrid.displayName = 'FlexGrid';

// Container component for consistent page layouts
export interface ContainerProps extends BoxProps {
  size?: 'small' | 'medium' | 'large' | 'xlarge' | 'fluid';
  disableGutters?: boolean;
}

const StyledContainer = styled(Box)<ContainerProps>(
  ({ theme, size, disableGutters }) => {
    const maxWidths = {
      small: '640px',
      medium: '768px',
      large: '1024px',
      xlarge: '1280px',
      fluid: '100%',
    };

    return {
      width: '100%',
      maxWidth: maxWidths[size || 'large'],
      margin: '0 auto',
      paddingLeft: disableGutters ? 0 : spacing.layout.container.paddingX.mobile,
      paddingRight: disableGutters ? 0 : spacing.layout.container.paddingX.mobile,
      
      [breakpoints.up.sm]: {
        paddingLeft: disableGutters ? 0 : spacing.layout.container.paddingX.tablet,
        paddingRight: disableGutters ? 0 : spacing.layout.container.paddingX.tablet,
      },
      
      [breakpoints.up.lg]: {
        paddingLeft: disableGutters ? 0 : spacing.layout.container.paddingX.desktop,
        paddingRight: disableGutters ? 0 : spacing.layout.container.paddingX.desktop,
      },
    };
  }
);

export const Container = forwardRef<HTMLDivElement, ContainerProps>(
  ({ children, ...props }, ref) => {
    return (
      <StyledContainer ref={ref} {...props}>
        {children}
      </StyledContainer>
    );
  }
);

Container.displayName = 'Container';

// Stack component for vertical layouts
export interface StackProps extends BoxProps {
  spacing?: number;
  direction?: 'column' | 'row';
  alignItems?: 'flex-start' | 'center' | 'flex-end' | 'stretch';
  justifyContent?: 'flex-start' | 'center' | 'flex-end' | 'space-between' | 'space-around';
  divider?: React.ReactNode;
}

const StyledStack = styled(Box)<StackProps>(
  ({ theme, spacing: stackSpacing, direction, alignItems, justifyContent }) => {
    const gap = stackSpacing ? `${stackSpacing * 4}px` : spacing.scale[2];

    return {
      display: 'flex',
      flexDirection: direction || 'column',
      gap,
      alignItems,
      justifyContent,
    };
  }
);

export const Stack = forwardRef<HTMLDivElement, StackProps>(
  ({ children, divider, ...props }, ref) => {
    if (divider && React.Children.count(children) > 1) {
      const childrenArray = React.Children.toArray(children);
      const childrenWithDividers = childrenArray.reduce<React.ReactNode[]>((acc, child, index) => {
        acc.push(child);
        if (index < childrenArray.length - 1) {
          acc.push(React.cloneElement(divider as React.ReactElement, { key: `divider-${index}` }));
        }
        return acc;
      }, []);

      return (
        <StyledStack ref={ref} {...props}>
          {childrenWithDividers}
        </StyledStack>
      );
    }

    return (
      <StyledStack ref={ref} {...props}>
        {children}
      </StyledStack>
    );
  }
);

Stack.displayName = 'Stack';

export default { GridContainer, GridItem, FlexGrid, Container, Stack };