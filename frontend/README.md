# Ad Mint AI - Frontend

React + TypeScript + Vite frontend for the Ad Mint AI application.

> **Note**: For complete setup and running instructions, see the [root README](../README.md).

## Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Run tests
npm run test
```

The application will be available at http://localhost:5173

## Tech Stack

- **React 19** - UI framework
- **TypeScript 5.9** - Type safety
- **Vite 5.4** - Build tool and dev server
- **Tailwind CSS 4** - Styling
- **Zustand 5** - State management
- **React Router 7** - Routing
- **Axios 1.13** - HTTP client
- **Vitest 1.6** - Testing framework

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build locally
- `npm run lint` - Run ESLint
- `npm run test` - Run tests
- `npm run test:ui` - Run tests with UI
- `npm run test:coverage` - Run tests with coverage report

## Project Structure

```
src/
├── components/
│   ├── layout/           # Layout components (Navbar, etc.)
│   ├── ui/               # Reusable UI components (Button, Input, etc.)
│   └── ProtectedRoute.tsx
├── routes/
│   ├── Auth/             # Authentication pages
│   │   ├── Login.tsx
│   │   └── Register.tsx
│   ├── Dashboard.tsx
│   ├── Gallery.tsx
│   └── Profile.tsx
├── store/
│   └── authStore.ts      # Zustand authentication store
├── lib/
│   ├── apiClient.ts      # Axios instance with interceptors
│   ├── authService.ts    # Authentication API calls
│   ├── config.ts         # API endpoints configuration
│   └── types/            # TypeScript type definitions
├── __tests__/            # Test files
├── App.tsx               # Main application component
├── main.tsx              # Application entry point
└── index.css             # Global styles with Tailwind
```

## Key Features

- **JWT Authentication**: Token-based auth with automatic refresh
- **Protected Routes**: Route guards for authenticated pages
- **Responsive Design**: Mobile-first design with Tailwind CSS
- **Form Validation**: Real-time validation on forms
- **Error Handling**: Comprehensive error handling with user feedback
- **Testing**: Unit and integration tests with Vitest
- **TypeScript**: Full type safety across the application

## Environment Variables

Create a `.env` file in the frontend directory:

```bash
# API base URL (defaults to http://localhost:8000)
VITE_API_URL=http://localhost:8000
```

## Development Notes

### Node.js Version

This project requires Node.js 20.19+ or 22.12+ due to Vite 5.4+ requirements.

### Tailwind CSS Configuration

Tailwind CSS v4 is configured with PostCSS. The configuration is in `postcss.config.js`.

### API Integration

The frontend communicates with the FastAPI backend through:
- `apiClient.ts` - Axios instance with request/response interceptors
- `authService.ts` - Authentication-related API calls
- Token stored in localStorage for persistent sessions

## Troubleshooting

### Port Already in Use

Vite will automatically use the next available port if 5173 is busy.

### Tailwind Styles Not Loading

1. Ensure `postcss.config.js` exists
2. Check that `@import "tailwindcss";` is in `index.css`
3. Restart the dev server

### CORS Errors

Verify the backend CORS configuration includes your frontend URL (default: `http://localhost:5173`).

## For More Information

- See the [root README](../README.md) for complete documentation
- API documentation: http://localhost:8000/docs (when backend is running)
- [React Documentation](https://react.dev/)
- [Vite Documentation](https://vite.dev/)
- [Tailwind CSS Documentation](https://tailwindcss.com/)
