/**
 * URL Compression Utilities
 * Handles compression and decompression for shareable URLs
 */

class URLCompression {
    /**
     * Compress a string using gzip compression
     * @param {string} str - The string to compress
     * @returns {Promise<string>} - Base64 encoded compressed string
     */
    static async compress(str) {
        try {
            // Convert string to Uint8Array
            const encoder = new TextEncoder();
            const data = encoder.encode(str);

            // Create compression stream
            const compressionStream = new CompressionStream('gzip');
            const writer = compressionStream.writable.getWriter();
            const reader = compressionStream.readable.getReader();

            // Compress the data
            writer.write(data);
            writer.close();

            // Read compressed data
            const chunks = [];
            let done = false;
            while (!done) {
                const { value, done: readerDone } = await reader.read();
                done = readerDone;
                if (value) {
                    chunks.push(value);
                }
            }

            // Combine chunks and encode to base64
            const compressed = new Uint8Array(chunks.reduce((acc, chunk) => acc + chunk.length, 0));
            let offset = 0;
            for (const chunk of chunks) {
                compressed.set(chunk, offset);
                offset += chunk.length;
            }

            // Convert to base64 and make URL-safe
            return btoa(String.fromCharCode(...compressed))
                .replace(/\+/g, '-')
                .replace(/\//g, '_')
                .replace(/=/g, '');
        } catch (error) {
            console.warn('Compression failed, falling back to simple encoding:', error);
            // Fallback to simple base64 encoding
            return btoa(unescape(encodeURIComponent(str)))
                .replace(/\+/g, '-')
                .replace(/\//g, '_')
                .replace(/=/g, '');
        }
    }

    /**
     * Decompress a base64 encoded compressed string
     * @param {string} compressedStr - Base64 encoded compressed string
     * @returns {Promise<string>} - Decompressed string
     */
    static async decompress(compressedStr) {
        try {
            // Restore base64 padding and characters
            let base64 = compressedStr
                .replace(/-/g, '+')
                .replace(/_/g, '/');

            // Add padding if necessary
            while (base64.length % 4) {
                base64 += '=';
            }

            // Convert base64 to Uint8Array
            const binaryString = atob(base64);
            const data = new Uint8Array(binaryString.length);
            for (let i = 0; i < binaryString.length; i++) {
                data[i] = binaryString.charCodeAt(i);
            }

            // Create decompression stream
            const decompressionStream = new DecompressionStream('gzip');
            const writer = decompressionStream.writable.getWriter();
            const reader = decompressionStream.readable.getReader();

            // Decompress the data
            writer.write(data);
            writer.close();

            // Read decompressed data
            const chunks = [];
            let done = false;
            while (!done) {
                const { value, done: readerDone } = await reader.read();
                done = readerDone;
                if (value) {
                    chunks.push(value);
                }
            }

            // Combine chunks and decode to string
            const decompressed = new Uint8Array(chunks.reduce((acc, chunk) => acc + chunk.length, 0));
            let offset = 0;
            for (const chunk of chunks) {
                decompressed.set(chunk, offset);
                offset += chunk.length;
            }

            const decoder = new TextDecoder();
            return decoder.decode(decompressed);
        } catch (error) {
            console.warn('Decompression failed, trying simple decoding:', error);
            // Fallback to simple base64 decoding
            try {
                let base64 = compressedStr
                    .replace(/-/g, '+')
                    .replace(/_/g, '/');
                while (base64.length % 4) {
                    base64 += '=';
                }
                return decodeURIComponent(escape(atob(base64)));
            } catch (fallbackError) {
                console.error('Both compression and fallback decoding failed:', fallbackError);
                throw new Error('Failed to decompress URL data');
            }
        }
    }

    /**
     * Generate a compressed shareable URL
     * @param {string} baseUrl - The base URL
     * @param {Object} data - The data to compress and include in URL
     * @returns {Promise<string>} - The compressed shareable URL
     */
    static async generateShareableURL(baseUrl, data) {
        const jsonString = JSON.stringify(data);
        const compressed = await this.compress(jsonString);

        const params = new URLSearchParams();
        params.set('c', compressed); // 'c' for compressed

        return `${baseUrl}?${params.toString()}`;
    }

    /**
     * Parse compressed data from URL parameters
     * @param {URLSearchParams} params - URL search parameters
     * @returns {Promise<Object|null>} - Parsed data or null if not found/invalid
     */
    static async parseFromURL(params) {
        // Try compressed format first
        if (params.has('c')) {
            try {
                const compressedData = params.get('c');
                const jsonString = await this.decompress(compressedData);
                return JSON.parse(jsonString);
            } catch (error) {
                console.warn('Failed to parse compressed URL data:', error);
                return null;
            }
        }

        // Fallback to old 'files' parameter format
        if (params.has('files')) {
            try {
                const data = JSON.parse(decodeURIComponent(escape(atob(params.get('files')))));
                return data;
            } catch (error) {
                console.warn('Failed to parse legacy URL data:', error);
                return null;
            }
        }

        // Fallback to even older 'code' parameter format
        if (params.has('code')) {
            try {
                const code = decodeURIComponent(escape(atob(params.get('code'))));
                const lang = params.get('lang') || 'python';
                return {
                    lang: lang,
                    files: [{ name: `main.${this.getExtensionForLanguage(lang)}`, content: code }],
                    activeFile: `main.${this.getExtensionForLanguage(lang)}`
                };
            } catch (error) {
                console.warn('Failed to parse legacy code URL data:', error);
                return null;
            }
        }

        return null;
    }

    /**
     * Get file extension for a programming language
     * @param {string} language - Programming language
     * @returns {string} - File extension
     */
    static getExtensionForLanguage(language) {
        const extensions = {
            'python': 'py',
            'c': 'c',
            'cpp': 'cpp',
            'java': 'java',
            'javascript': 'js',
            'eiffel': 'e'
        };
        return extensions[language] || 'txt';
    }

    /**
     * Calculate compression ratio
     * @param {string} original - Original string
     * @param {string} compressed - Compressed string
     * @returns {number} - Compression ratio (0-1, where 0.5 means 50% compression)
     */
    static getCompressionRatio(original, compressed) {
        const originalSize = original.length;
        const compressedSize = compressed.length;
        return compressedSize / originalSize;
    }
}

// Check if compression is supported
URLCompression.isSupported = () => {
    return typeof CompressionStream !== 'undefined' && typeof DecompressionStream !== 'undefined';
};

// Export as global for backwards compatibility
window.URLCompression = URLCompression;
