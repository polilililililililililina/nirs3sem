import { AppProps } from 'next/app'
import Head from 'next/head'

import { Layout } from '@shared/ui/Layout'

import '../styles/index.css'

function MyApp({ Component, pageProps }: AppProps) {
  return (
    <>
      <Head>
        <title>MRI Analyzer</title>
        <meta name="description" content="Сервис анализа МРТ изображений" />
      </Head>

      <Layout>
        <Component {...pageProps} />
      </Layout>
    </>
  )
}

export default MyApp
