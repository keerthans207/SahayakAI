import { useTranslation } from "react-i18next";

import { Languages } from "lucide-react";



interface Language {

  code: string;

  native: string;

  rtl?: boolean;

}



const SUPPORTED_LANGUAGES: Language[] = [

  { code: "en", native: "English" },

  { code: "hi", native: "हिन्दी" },

];



export function LanguageSelector() {

  const { i18n } = useTranslation();



  const handleChange = (code: string) => {

    i18n.changeLanguage(code);

    // Set RTL if needed.

    const lang = SUPPORTED_LANGUAGES.find((l: Language) => l.code === code);

    document.documentElement.dir = lang?.rtl ? "rtl" : "ltr";

    document.documentElement.lang = code;

  };



  const current = SUPPORTED_LANGUAGES.find((l: Language) => l.code === i18n.language);



  return (

    <div className="relative">

      <label className="sr-only" htmlFor="language-select">Select language</label>

      <div className="flex items-center gap-1.5">

        <Languages className="h-4 w-4 shrink-0 text-gray-600" aria-hidden />

        <select

          id="language-select"

          value={i18n.language}

          onChange={(e) => handleChange(e.target.value)}

          className="cursor-pointer rounded-md border-none bg-transparent py-1 pl-1 pr-6 text-sm font-medium focus-visible:ring-2"

          aria-label="Language"

        >

          {SUPPORTED_LANGUAGES.map((l: Language) => (

            <option key={l.code} value={l.code}>

              {l.native}

            </option>

          ))}

        </select>

      </div>

    </div>

  );

}
