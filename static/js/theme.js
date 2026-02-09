/**
 * Theme management for Dungeon Buddy.
 * Handles toggling between light and dark modes using Bootstrap 5.3 data attributes.
 * Persists user preference in localStorage.
 */

(() => {
    'use strict'

    const getStoredTheme = () => localStorage.getItem('theme')
    const setStoredTheme = theme => localStorage.setItem('theme', theme)

    const getPreferredTheme = () => {
        const storedTheme = getStoredTheme()
        if (storedTheme) {
            return storedTheme
        }
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
    }

    const setTheme = theme => {
        document.documentElement.setAttribute('data-bs-theme', theme)
        updateIcon(theme)
    }

    const updateIcon = theme => {
        const themeIcon = document.getElementById('theme-icon-active')
        if (!themeIcon) return

        if (theme === 'dark') {
            themeIcon.classList.remove('bi-sun-fill')
            themeIcon.classList.add('bi-moon-stars-fill')
        } else {
            themeIcon.classList.remove('bi-moon-stars-fill')
            themeIcon.classList.add('bi-sun-fill')
        }
    }

    // Toggle event handler
    const setupThemeToggle = () => {
        const toggleBtn = document.getElementById('theme-toggle')
        if (!toggleBtn) return

        toggleBtn.addEventListener('click', () => {
            const currentTheme = document.documentElement.getAttribute('data-bs-theme')
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark'
            setStoredTheme(newTheme)
            setTheme(newTheme)
        })
    }

    // Initial setup on DOMContentLoaded
    window.addEventListener('DOMContentLoaded', () => {
        setTheme(getPreferredTheme())
        setupThemeToggle()
    })

    // Listen for system preference changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
        const storedTheme = getStoredTheme()
        if (storedTheme !== 'light' && storedTheme !== 'dark') {
            setTheme(getPreferredTheme())
        }
    })
})()
