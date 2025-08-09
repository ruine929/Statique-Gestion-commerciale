# Gestion Commerciale - Commercial Management System

## Overview

This is a comprehensive commercial management application built with Python Flask, designed to automate and track complete business operations from purchasing to sales. The system provides inventory management, sales tracking, customer management, and detailed business analytics with low stock alerts and financial reporting capabilities.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Framework**: Flask web framework with SQLAlchemy ORM
- **Database**: SQLite for development with PostgreSQL compatibility for production
- **Authentication**: Google OAuth 2.0 integration using oauthlib for secure user authentication
- **Session Management**: Flask-Login for user session handling
- **Application Structure**: Modular blueprint-based architecture separating concerns into distinct route modules

### Data Model Design
- **Core Entities**: Products (Produit), Sales (Vente), Purchases (Achat), and Clients
- **Inventory Tracking**: Real-time stock management with automatic updates on transactions
- **Financial Calculations**: Automated profit margin calculations, commercial balance tracking, and pricing management
- **Alert System**: Configurable low stock thresholds with automatic notifications

### Service Layer Architecture
- **Business Logic Separation**: Dedicated service classes (StockService, VenteService, AchatService, StatistiqueService, AlerteService)
- **Transaction Management**: Centralized database transaction handling with rollback capabilities
- **Statistics Engine**: Comprehensive reporting system with period-based analytics and performance metrics

### Frontend Architecture
- **Template Engine**: Jinja2 templating with Bootstrap 5 for responsive design
- **UI Components**: Font Awesome icons, Chart.js for data visualization
- **User Experience**: Dashboard-driven interface with real-time alerts and status indicators
- **Data Export**: CSV/JSON export capabilities for reporting

### Configuration Management
- **Environment-based Config**: Separate configuration for development and production environments
- **Currency Handling**: Malagasy Ariary (MGA) as primary currency with proper formatting
- **Pagination**: Configurable page sizes for data listing views

## External Dependencies

### Authentication Services
- **Google OAuth 2.0**: Complete integration for user authentication and registration
- **Required Setup**: Google Cloud Console OAuth client configuration with proper redirect URIs

### Database Systems
- **Development**: SQLite database for local development and testing
- **Production Ready**: PostgreSQL compatibility with connection pooling and health checks
- **ORM**: SQLAlchemy with declarative base for database abstraction

### Frontend Libraries
- **Bootstrap 5**: Responsive UI framework with dark theme support
- **Font Awesome 6**: Icon library for consistent visual elements
- **Chart.js**: JavaScript charting library for statistical visualizations

### Python Packages
- **Flask Ecosystem**: Flask-SQLAlchemy, Flask-Login for core functionality
- **OAuth Library**: oauthlib for Google authentication implementation
- **Database**: SQLAlchemy ORM with relationship management
- **Utilities**: Werkzeug for WSGI middleware and request handling