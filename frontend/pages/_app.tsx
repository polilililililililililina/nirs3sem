import { AppProps } from 'next/app'
import Head from 'next/head'

import '../styles/index.css'

function MyApp({ Component, pageProps }: AppProps) {
  return (
    <>
      <Head>
        <title>MRI Analyzer</title>

        <meta name="description" content="Сервис анализа МРТ изображений" />
      </Head>
      <Component {...pageProps} />
    </>
  )
}

export default MyApp
