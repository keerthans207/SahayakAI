import i18n from 'i18next';

import { initReactI18next } from 'react-i18next';

import LanguageDetector from 'i18next-browser-languagedetector';



i18n

  .use(LanguageDetector)

  .use(initReactI18next)

  .init({

    resources: {

      en: {

        translation: {

          common: {

            loading: 'Loading...',

            save: 'Save',

            cancel: 'Cancel',

            delete: 'Delete',

            edit: 'Edit',

            view: 'View',

            search: 'Search',

            filter: 'Filter',

            filters: 'Filters',

            submit: 'Submit',

            back: 'Back',

            next: 'Next',

            previous: 'Previous',

            close: 'Close',

            confirm: 'Confirm',

            error: 'Error',

            success: 'Success',

            all: 'All',

            clearFilters: 'Clear Filters',

            page: 'Page',

            of: 'of',

            viewAll: 'View All',

            searchSchemes: 'Search schemes...',

            needs_verification: 'Needs Verification',

          },

          nav: {

            dashboard: 'Dashboard',

            assistant: 'AI Assistant',

            schemes: 'Schemes',

            documents: 'Documents',

            applications: 'Applications',

            profile: 'Profile',

            settings: 'Settings',

            logout: 'Logout',

          },

          landing: {

            title: 'Welcome to SahayakAI',

            subtitle: 'Your intelligent assistant for Indian government schemes',

            feature1: 'Discover eligible government schemes',

            feature2: 'AI-powered guidance in English and Hindi',

            feature3: 'Track your applications easily',

          },

          auth: {

            login: 'Login',

            register: 'Sign Up',

            logout: 'Logout',

            email: 'Email',

            password: 'Password',

            fullName: 'Full Name',

            phone: 'Phone Number',

            loginDescription: 'Enter your credentials to access your account',

            registerDescription: 'Create a new account to get started',

            loginSuccess: 'Login successful!',

            loginError: 'Login failed. Please check your credentials.',

            registerSuccess: 'Registration successful!',

            registerError: 'Registration failed. Please try again.',

            noAccount: "Don't have an account?",

            hasAccount: 'Already have an account?',

          },

          dashboard: {

            title: 'Dashboard',

            welcome: 'Welcome back, {{name}}!',

            welcomeMessage: 'Your personalized assistant for finding and applying to government schemes effortlessly. Simple, accessible, and trust-driven.',

            discoverSchemes: 'Discover Government Schemes',

            askSahayak: 'Ask Sahayak AI',

            quickActionsTitle: 'Quick Actions',

            quickActions: {

              discoverSchemes: 'Discover Schemes',

              discoverSchemesDesc: 'Browse through thousands of state and central schemes',

              checkEligibility: 'Check Eligibility',

              checkEligibilityDesc: 'Find out which schemes you are eligible for',

              uploadDocuments: 'Upload Documents',

              uploadDocumentsDesc: 'Securely store and track your required documents',

              trackApplications: 'Track Applications',

              trackApplicationsDesc: 'Get real-time alerts about application status',

            },

            recommendedSchemes: 'Recommended Schemes',

            noSchemes: 'No schemes available',

            noSchemesDesc: 'We are still building our database. Check back soon!',

            browseSchemes: 'Browse All Schemes',

            applicationsOverview: 'Applications Overview',

            noApplications: 'No applications yet',

            noApplicationsDesc: 'Start discovering schemes to apply for benefits.',

            startApplication: 'Start an Application',

            viewAllApplications: 'View all {{count}} applications',

            aiAssistant: 'AI Assistant',

            aiAssistantDesc: 'Get personalized help finding the right schemes for you.',

            startConversation: 'Start Conversation',

            infoTitle: 'Always Verify Information',

            infoMessage: 'Sahayak AI provides helpful guidance, but always verify details with official government sources before applying.',

            schemes: 'Available Schemes',

            schemesDescription: 'Schemes you may be eligible for',

            applications: 'My Applications',

            applicationsDescription: 'Track your application status',

            documents: 'My Documents',

            documentsDescription: 'Uploaded documents',

          },

          assistant: {

            title: 'Sahayak AI Assistant',

            subtitle: 'Your intelligent guide to government schemes',

            placeholder: 'Ask me about government schemes...',

            welcomeTitle: 'How can I help you today?',

            welcomeMessage: 'I can help you find government schemes, check eligibility, understand application requirements, and answer questions about benefits.',

            capability1: 'Find schemes based on your profile and needs',

            capability2: 'Check your eligibility for specific schemes',

            capability3: 'Understand application requirements and documents',

            capability4: 'Get guidance in English, Hindi, and other languages',

            suggestedPrompts: 'Try asking me',

            startConversation: 'Start a New Conversation',

            chatInterfaceTitle: 'Chat Interface Coming Soon',

            chatInterfaceDesc: 'The full chat interface is being integrated. For now, you can see your selected prompt here.',

            selectedPrompt: 'Selected prompt',

          },

          schemes: {

            title: 'Government Schemes',

            description: 'Discover and explore government welfare schemes available to you',

            placeholder: 'Browse available schemes',

            details: 'Scheme Details',

            searchPlaceholder: 'Search schemes by name, category, or keywords...',

            category: 'Category',

            governmentLevel: 'Government Level',

            stateLabel: 'State',

            statusLabel: 'Status',

            central: 'Central',

            active: 'Active',

            inactive: 'Inactive',

            noResults: 'No schemes found',

            noResultsDesc: 'Try adjusting your filters or search query.',

            errorLoading: 'Failed to load schemes. Please try again.',

            resultsCount: '{{count}} schemes found',

            check_eligibility: 'Check Eligibility',

            categories: {

              education: 'Education',

              health: 'Health',

              disability: 'Disability',

              employment: 'Employment',

              social_welfare: 'Social Welfare',

              housing: 'Housing',

              agriculture: 'Agriculture',

              financial: 'Financial',

            },

          },

          documents: {

            title: 'My Documents',

            placeholder: 'Upload and manage your documents',

          },

          applications: {

            title: 'My Applications',

            placeholder: 'View and track your applications',

            details: 'Application Details',

            status: {

              discovered: 'Discovered',

              eligibility_pending: 'Checking Eligibility',

              eligible_pending_documents: 'Eligible - Upload Documents',

              documents_incomplete: 'Documents Incomplete',

              ready_for_review: 'Ready for Review',

              ready_for_user_submission: 'Ready to Submit',

              submitted_by_user: 'Submitted',

              under_verification: 'Under Verification',

              approved: 'Approved',

              rejected: 'Rejected',

              closed: 'Closed',

            },

          },

          profile: {

            title: 'My Profile',

            information: 'Personal Information',

          },

          settings: {

            title: 'Settings',

            placeholder: 'Manage your preferences',

          },

          eligibility: {

            title: 'Eligibility Check',

            placeholder: 'Check your eligibility for schemes',

          },

        },

      },

      hi: {

        translation: {

          common: {

            loading: 'लोड हो रहा है...',

            save: 'सहेजें',

            cancel: 'रद्द करें',

            delete: 'हटाएं',

            edit: 'संपादित करें',

            view: 'देखें',

            search: 'खोजें',

            filter: 'फ़िल्टर',

            submit: 'जमा करें',

            back: 'वापस',

            next: 'अगला',

            previous: 'पिछला',

            close: 'बंद करें',

            confirm: 'पुष्टि करें',

            error: 'त्रुटि',

            success: 'सफलता',

          },

          nav: {

            dashboard: 'डैशबोर्ड',

            assistant: 'AI सहायक',

            schemes: 'योजनाएं',

            documents: 'दस्तावेज़',

            applications: 'आवेदन',

            profile: 'प्रोफ़ाइल',

            settings: 'सेटिंग',

            logout: 'लॉग आउट',

          },

          landing: {

            title: 'सहायकAI में आपका स्वागत है',

            subtitle: 'भारतीय सरकारी योजनाओं के लिए आपका बुद्धिमान सहायक',

            feature1: 'पात्र सरकारी योजनाएं खोजें',

            feature2: 'अंग्रेजी और हिंदी में AI-संचालित मार्गदर्शन',

            feature3: 'अपने आवेदनों को आसानी से ट्रैक करें',

          },

          auth: {

            login: 'लॉगिन',

            register: 'साइन अप',

            logout: 'लॉग आउट',

            email: 'ईमेल',

            password: 'पासवर्ड',

            fullName: 'पूरा नाम',

            phone: 'फ़ोन नंबर',

            loginDescription: 'अपने खाते तक पहुँचने के लिए अपनी जानकारी दर्ज करें',

            registerDescription: 'शुरू करने के लिए एक नया खाता बनाएं',

            loginSuccess: 'लॉगिन सफल रहा!',

            loginError: 'लॉगिन विफल। कृपया अपनी जानकारी जांचें।',

            registerSuccess: 'पंजीकरण सफल रहा!',

            registerError: 'पंजीकरण विफल। कृपया पुनः प्रयास करें।',

            noAccount: 'खाता नहीं है?',

            hasAccount: 'पहले से खाता है?',

          },

          dashboard: {

            title: 'डैशबोर्ड',

            schemes: 'उपलब्ध योजनाएं',

            schemesDescription: 'जिन योजनाओं के लिए आप पात्र हो सकते हैं',

            applications: 'मेरे आवेदन',

            applicationsDescription: 'अपने आवेदन की स्थिति ट्रैक करें',

            documents: 'मेरे दस्तावेज़',

            documentsDescription: 'अपलोड किए गए दस्तावेज़',

          },

          assistant: {

            title: 'AI सहायक',

            placeholder: 'मुझसे सरकारी योजनाओं के बारे में पूछें...',

          },

          schemes: {

            title: 'सरकारी योजनाएं',

            placeholder: 'उपलब्ध योजनाएं ब्राउज़ करें',

            details: 'योजना विवरण',

          },

          documents: {

            title: 'मेरे दस्तावेज़',

            placeholder: 'अपने दस्तावेज़ अपलोड और प्रबंधित करें',

          },

          applications: {

            title: 'मेरे आवेदन',

            placeholder: 'अपने आवेदन देखें और ट्रैक करें',

            details: 'आवेदन विवरण',

          },

          profile: {

            title: 'मेरी प्रोफ़ाइल',

            information: 'व्यक्तिगत जानकारी',

          },

          settings: {

            title: 'सेटिंग',

            placeholder: 'अपनी प्राथमिकताएं प्रबंधित करें',

          },

          eligibility: {

            title: 'पात्रता जांच',

            placeholder: 'योजनाओं के लिए अपनी पात्रता जांचें',

          },

        },

      },

    },

    fallbackLng: 'en',

    debug: false,

    interpolation: {

      escapeValue: false,

    },

    detection: {

      order: ['localStorage', 'navigator'],

      caches: ['localStorage'],

    },

  });



export default i18n;
