
GOV.UK  Content API  **Beta**

  * Getting Started
  * Reference

  * GOV.UK Content API
    * What you can do with this API
    * What you can’t do with this API
    * Quick start
    * Beta software
    * Authentication
    * Security and compliance
      * Reporting vulnerabilities
      * HTTPS
      * Security patches
    * Rate limiting
    * Support

# GOV.UK Content API

**Beta** This is a trial service — your feedback will help us to improve it. Find out what this means.

GOV.UK Content API makes it possible to access the data used to render content on https://www.gov.uk (hereafter referred to as GOV.UK). For any page hosted on GOV.UK you can use the path to access the content and associated metadata for a page.

GOV.UK Content API is accessed via HTTP and returns data in a JSON format. The reference documentation details the endpoints and the response format.

## What you can do with this API

This API is useful for applications that incorporate content from GOV.UK and for keeping that content up to date. It provides a more accessible and predictable interface than what can be achieved through scraping HTML pages.

You can navigate between content within this API by utilising links. For example, for a page you could access the government organisation that published the page and then navigate to feature policies of that organisation.

## What you can’t do with this API

The content within this API is limited to pages hosted on `www.gov.uk` and does not include other websites that are subdomains of `gov.uk`.

This API includes only the pages on GOV.UK that are available as HTML and does not allow direct access to attachments or images. These files however are associated with their HTML content and can be accessed.

Not all content is available. For example, content that is generated dynamically (such as through a search) is not available. Some types of content may still be being migrated to utilise this API and these could appear as placeholder documents without any content or as redirections to a catch-all content item that represents a group of unmigrated content.

If you wish to access historic content this can currently be done through the National Archives.

## Quick start

You can use the GOV.UK Content API to look up the data that is used to render content on GOV.UK.

To get started:

  1. Pick a page on GOV.UK, for example: https://www.gov.uk/take-pet-abroad.
  2. Make a note of the path, for example: `/take-pet-abroad`.
  3. Using a tool such as curl, Postman or your web browser, make a GET request to `https://www.gov.uk/api/content/take-pet-abroad`.
  4. You’ll receive a JSON response and the fields for this are explained in the reference documentation.

For example, using the curl command line utility tool:

```
curl https://www.gov.uk/api/content/take-pet-abroad

```

Or, you can use the govuk-browser-extension. Note that this is intended for internal use.

## Beta software

GOV.UK Content API is currently beta software and may be subject to changes and improvements as we learn from usage.

This means that you may use this software and build applications that utilise it. However as we learn from feedback we may make changes to the software.

Please use our survey if you would like to share your feedback about GOV.UK Content API.

## Authentication

Usage of GOV.UK Content API does not require authentication.

## Security and compliance

### Reporting vulnerabilities

If you believe there is a security issue with GOV.UK Content API, read our security policy and contact us immediately.

Please don’t disclose the suspected breach publicly until it has been fixed.

### HTTPS

GOV.UK Content API follows government HTTPS security guidelines. The Hypertext Transfer Protocol Secure (HTTPS), which involves the Transport Layer Security (TLS) protocol, is used by the platform to provide secure connections.

### Security patches

We treat security vulnerabilities in the platform and library code in the GOV.UK Content API as our highest priority. The codebase will be updated as soon as possible when vulnerabilities are discovered or reported.

We frequently upgrade the framework and library code in GOV.UK Content API to the latest versions for security and feature enhancements.

## Rate limiting

There is a maximum limit of 10 requests per second per client. If you exceed this your request won’t be processed until the limit is no longer exceeded and you may see timeout errors.

We think this should be sufficient for all users of GOV.UK Content API but if you believe you need the limit increasing you can contact support.

## Support

GOV.UK Content API is currently in a beta phase and may be subject to changes and improvements.

If you experience any issues or have questions regarding GOV.UK Content API please:

  * **If you are a government department:** Raise a ticket with GOV.UK Support
  * **Otherwise:** Contact GOV.UK with your query

  * Accessibility

All content is available under the Open Government Licence v3.0, except where otherwise stated
