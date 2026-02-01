/**
 * UI Components Index
 *
 * This file exports all base UI components, providing a single import point
 * for the entire component library.
 */

// Button component
export {
  Button,
  buttonVariants,
  type ButtonProps,
} from './Button';

// Input component
export {
  Input,
  inputVariants,
  type InputProps,
} from './Input';

// Card component
export {
  Card,
  CardHeader,
  CardFooter,
  CardTitle,
  CardDescription,
  CardContent,
  CardActions,
  CardSkeleton,
  type CardProps,
  type CardHeaderProps,
  type CardTitleProps,
  type CardDescriptionProps,
  type CardContentProps,
  type CardFooterProps,
  type CardActionsProps,
  type CardSkeletonProps,
} from './Card';

// Modal component
export {
  Modal,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ConfirmDialog,
  type ModalProps,
  type ModalHeaderProps,
  type ModalBodyProps,
  type ModalFooterProps,
  type ConfirmDialogProps,
} from './Modal';

// Progress component
export {
  LinearProgress,
  CircularProgress,
  ProgressGroup,
  linearProgressVariants,
  circularProgressVariants,
  type LinearProgressProps,
  type CircularProgressProps,
  type ProgressGroupProps,
} from './Progress';
