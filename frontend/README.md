# Skill Seekers Frontend

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/skillseekers/frontend)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://github.com/skillseekers/frontend/actions)
[![Coverage](https://img.shields.io/badge/coverage-85%25-brightgreen.svg)](https://github.com/skillseekers/frontend)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue.svg)](https://www.typescriptlang.org/)
[![React](https://img.shields.io/badge/React-18.2-blue.svg)](https://reactjs.org/)

Skill Seekers Frontend is a modern, enterprise-grade web application built with React 18, TypeScript, and Vite. It provides a comprehensive interface for managing AI skills across multiple LLM platforms with real-time progress tracking, advanced file management, and seamless user experience.

## ✨ Features

### 🎯 Core Features
- **Skill Management**: Create, edit, delete, and organize AI skills
- **Multi-Platform Support**: Claude, Gemini, OpenAI, and Markdown
- **Real-time Updates**: WebSocket integration for live progress tracking
- **File Editor**: Monaco Editor with syntax highlighting and auto-save
- **Download System**: Multi-platform packaging and download
- **Search & Filter**: Advanced filtering with debounced search
- **Responsive Design**: Mobile-first, responsive UI

### 🚀 Performance
- **Code Splitting**: Route-based and component-based lazy loading
- **Virtual Scrolling**: Handle 1000+ items smoothly
- **Bundle Optimization**: < 1MB bundle size, 500KB gzipped
- **Fast Loading**: < 2s initial load time
- **60fps Scrolling**: Optimized for smooth interactions
- **Lazy Loading**: Images and components load on demand

### ♿ Accessibility
- **WCAG 2.1 AA**: Full compliance
- **Keyboard Navigation**: Complete keyboard support
- **Screen Reader**: Compatible with all screen readers
- **ARIA Labels**: Comprehensive ARIA implementation
- **Focus Management**: Logical tab order and focus traps
- **Color Contrast**: Meets all contrast requirements

### 🔒 Security
- **Type Safety**: Full TypeScript coverage
- **Error Boundaries**: Graceful error handling
- **Input Validation**: Comprehensive validation
- **XSS Protection**: React's built-in protections
- **CSRF Protection**: Secure token handling
- **Content Security Policy**: Configurable CSP headers

### 🧪 Testing
- **85%+ Coverage**: Unit, integration, and E2E tests
- **Vitest**: Fast unit testing
- **Playwright**: Cross-browser E2E testing
- **axe-core**: Automated accessibility testing
- **CI/CD Integration**: Automated testing pipeline

## 🏗️ Tech Stack

### Core
- **React 18.2+**: Modern React with hooks and concurrent features
- **TypeScript 5.0+**: Type-safe development
- **Vite 4.5+**: Fast build tool and dev server

### UI & Styling
- **Tailwind CSS**: Utility-first CSS framework
- **Radix UI**: Unstyled, accessible components
- **Heroicons**: Beautiful SVG icons
- **Lucide React**: Modern icon library

### State Management
- **Zustand**: Lightweight state management
- **React Query**: Server state management
- **React Router**: Client-side routing

### Development Tools
- **ESLint**: Code linting
- **Prettier**: Code formatting
- **Vitest**: Unit testing framework
- **Playwright**: E2E testing
- **Husky**: Git hooks

## 📦 Project Structure

```
src/
├── app/                      # Application entry point
│   └── App.tsx              # Root component
├── components/              # Reusable components
│   ├── ui/                  # Base UI components
│   │   ├── Button.tsx
│   │   ├── Input.tsx
│   │   ├── Modal.tsx
│   │   └── ...
│   ├── features/            # Feature components
│   │   ├── skill-card/
│   │   ├── skill-list/
│   │   ├── skill-create-wizard/
│   │   └── ...
│   └── shared/              # Shared components
├── hooks/                   # Custom React hooks
│   ├── useSkills.ts
│   ├── useWebSocket.ts
│   └── ...
├── stores/                  # Zustand stores
│   ├── uiStore.ts
│   ├── skillStore.ts
│   └── ...
├── utils/                   # Utility functions
│   ├── accessibility.ts
│   ├── memoization.ts
│   ├── performance-monitoring.ts
│   └── ...
├── types/                   # TypeScript type definitions
│   ├── index.ts
│   ├── skill.types.ts
│   └── ...
├── styles/                  # Global styles
│   └── index.css
└── test/                   # Test utilities
    ├── setup.ts
    ├── test-utils.tsx
    └── ...
```

## 🚀 Quick Start

### Prerequisites
- **Node.js**: 18.0.0 or higher
- **npm**: 8.0.0 or higher

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/skillseekers/frontend.git
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Start development server**
   ```bash
   npm run dev
   ```

5. **Open in browser**
   ```
   http://localhost:3000
   ```

## 📖 Available Scripts

### Development
```bash
# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Type checking
npm run type-check
```

### Testing
```bash
# Run unit tests
npm test

# Run tests with UI
npm run test:ui

# Run tests with coverage
npm run test:coverage

# Run tests in watch mode
npm run test:watch

# Run all tests
npm run test:all

# Run E2E tests
npm run test:e2e

# Run E2E tests with UI
npm run test:e2e:ui

# Run accessibility tests
npm run test:a11y
```

### Code Quality
```bash
# Lint code
npm run lint

# Fix linting issues
npm run lint:fix

# Format code
npm run format

# Check formatting
npm run format:check
```

### Performance
```bash
# Analyze bundle
npm run build:analyze

# Performance report
npm run perf:report

# Performance check
npm run perf:check
```

## 🐳 Docker Deployment

### Quick Start
```bash
# Build and deploy
./deploy.sh deploy

# Check status
./deploy.sh status

# View logs
./deploy.sh logs
```

### Docker Commands
```bash
# Build image
docker build -t skillseekers-frontend .

# Run container
docker run -p 3000:80 skillseekers-frontend

# Docker Compose
docker-compose up -d

# With monitoring
docker-compose --profile monitoring up -d
```

See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed deployment instructions.

## 🎨 Design System

### Colors
- **Claude**: #D97706 (Orange)
- **Gemini**: #1A73E8 (Blue)
- **OpenAI**: #10A37F (Green)
- **Markdown**: #6B7280 (Gray)

### Typography
- **Primary Font**: Inter (Sans-serif)
- **Code Font**: JetBrains Mono (Monospace)
- **Scale**: 4/8px base unit system

### Components
All components follow these principles:
- **Accessible**: WCAG 2.1 AA compliant
- **Composable**: Reusable and flexible
- **Themeable**: Support for custom themes
- **Responsive**: Mobile-first design
- **Type-safe**: Full TypeScript support

## 🧪 Testing

### Test Structure
- **Unit Tests**: Component and function tests
- **Integration Tests**: Component interaction tests
- **E2E Tests**: Full user journey tests
- **Accessibility Tests**: Automated a11y testing

### Running Tests
```bash
# All tests
npm test

# Coverage report
npm run test:coverage

# Watch mode
npm run test:watch

# E2E tests
npm run test:e2e

# Accessibility tests
npm run test:a11y
```

### Test Coverage
- **Lines**: 85%
- **Functions**: 85%
- **Branches**: 85%
- **Statements**: 85%

## ♿ Accessibility

### Standards
- **WCAG 2.1 AA**: Full compliance
- **Section 508**: US government standard
- **ADA**: Americans with Disabilities Act

### Features
- Keyboard navigation
- Screen reader support
- Focus management
- Color contrast
- ARIA labels
- Skip links

### Testing
Automated testing with axe-core:
```bash
npm run test:a11y
```

## 📊 Performance

### Metrics
- **Initial Load**: < 2 seconds
- **Time to Interactive**: < 3 seconds
- **Largest Contentful Paint**: < 2.5 seconds
- **Bundle Size**: < 1MB (500KB gzipped)
- **Scroll Performance**: 60fps

### Optimization
- Code splitting
- Lazy loading
- Virtual scrolling
- Image optimization
- Memoization
- Debouncing

### Monitoring
```bash
# Performance report
npm run perf:report

# Bundle analysis
npm run build:analyze
```

See [PERFORMANCE.md](./PERFORMANCE.md) for detailed performance guide.

## 🔧 Configuration

### Environment Variables
```bash
# API Configuration
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000

# Application
VITE_APP_VERSION=1.0.0
NODE_ENV=development
```

See [.env.example](./.env.example) for all options.

### Build Configuration
- **Vite**: `vite.config.ts`
- **TypeScript**: `tsconfig.json`
- **ESLint**: `.eslintrc.js`
- **Prettier**: `.prettierrc`

## 🚀 Deployment

### Production Build
```bash
npm run build
```

### Docker Deployment
```bash
./deploy.sh deploy
```

### Environment-Specific
```bash
# Production
./deploy.sh --env production deploy

# Staging
./deploy.sh --env staging deploy

# Development
./deploy.sh --env development deploy
```

See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed deployment guide.

## 📚 Documentation

### Guides
- [DEPLOYMENT.md](./DEPLOYMENT.md) - Deployment guide
- [PERFORMANCE.md](./PERFORMANCE.md) - Performance guide
- [TESTING_STRATEGY.md](./TESTING_STRATEGY.md) - Testing guide
- [ACCESSIBILITY.md](./src/utils/ACCESSIBILITY.md) - Accessibility guide

### API Documentation
- [API.md](./API.md) - API reference
- Inline JSDoc comments
- Storybook (coming soon)

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write/update tests
5. Run linting and tests
6. Submit a pull request

### Code Style
- Use TypeScript for all new code
- Follow ESLint and Prettier configurations
- Write tests for new features
- Update documentation
- Follow conventional commit messages

### Commit Messages
```
feat: add new skill creation wizard
fix: resolve memory leak in skill list
docs: update API documentation
test: add integration tests for WebSocket
refactor: optimize performance monitoring
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- React team for the amazing framework
- Vite team for the lightning-fast build tool
- Radix UI for accessible components
- All contributors who have helped improve this project

## 📞 Support

- **Documentation**: [./docs](./docs)
- **Issues**: [GitHub Issues](https://github.com/skillseekers/frontend/issues)
- **Discussions**: [GitHub Discussions](https://github.com/skillseekers/frontend/discussions)
- **Email**: support@skillseekers.io

## 🗺️ Roadmap

### Version 1.1
- [ ] Storybook integration
- [ ] Theme customization
- [ ] Advanced analytics
- [ ] Plugin system

### Version 1.2
- [ ] Offline support
- [ ] PWA features
- [ ] Advanced filters
- [ ] Bulk operations

### Version 2.0
- [ ] Multi-language support
- [ ] Advanced collaboration
- [ ] Enterprise features
- [ ] Custom workflows

---

<div align="center">

**[Website](https://skillseekers.io)** ·
**[Documentation](./docs)** ·
**[API](./API.md)** ·
**[Issues](https://github.com/skillseekers/frontend/issues)** ·
**[Discussions](https://github.com/skillseekers/frontend/discussions)**

Made with ❤️ by the Skill Seekers Team

</div>
