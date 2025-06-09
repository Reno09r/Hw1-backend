/// <reference types="vitest" />
/// <reference types="@testing-library/jest-dom" />

import '@testing-library/jest-dom'
import { expect, afterEach } from 'vitest'
import { cleanup } from '@testing-library/react'
import * as matchers from '@testing-library/jest-dom/matchers'

// Расширяем expect всеми матчерами из jest-dom
Object.entries(matchers).forEach(([name, matcher]) => {
  expect.extend({ [name]: matcher })
})

afterEach(() => {
  cleanup()
}) 