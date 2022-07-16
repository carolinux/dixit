import '@testing-library/jest-dom/extend-expect';
import 'core-js/modules/es7.promise.finally';
import 'jest-fetch-mock';
import httpAdapter from 'axios/lib/adapters/http'

global.fetch = require('jest-fetch-mock');
axios.defaults.baseURL = 'http://localhost:5000';
axios.defaults.adapter = httpAdapter;