/** @type {import('tailwindcss').Config} */
export default {
    content: ["./index.html", "./src/**/*.{js,jsx}"],
    theme: {
        extend: {
            fontFamily: {
                sans: ["'Lucida Sans Unicode'", "'Lucida Grande'", "'Lucida Sans'", "Geneva", "Verdana", "sans-serif"],
            },
            colors: {
                // Netflix color palette
                netflix: {
                    red: '#e50914',
                    black: '#141414',
                    dark: '#1f1f1f',
                    gray: '#333333',
                }
            },
        },
    },
    plugins: [],
}
