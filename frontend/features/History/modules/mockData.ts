import { MriAnalysisRequest } from "../types"


export const mockMriRequests: MriAnalysisRequest[] = [
  {
    id: '1',
    inputImage: 'img/1.jpg',
    outputImage: 'img/2.jpg',
    description: 'На серии МРТ снимков головного мозга определяется объёмное образование в правой височной доле размером 2.3×1.8 см с неоднородным усилением сигнала. Отмечается перифокальный отёк. Срединные структуры не смещены. Желудочковая система не изменена.',
    createdAt: '2024-01-15T10:30:00Z',
    status: 'completed',
    anomalies: ['Опухоль', 'Отёк'],
    confidence: 92,
    recommendations: ['Консультация нейрохирурга', 'Повторное МРТ через 3 месяца']
  },
  {
    id: '2',
    inputImage: 'img/1.jpg',
    outputImage: 'img/2.jpg',
    description: 'Выявлены множественные очаги демиелинизации в перивентрикулярных зонах и мозолистом теле. Размеры очагов от 3 до 8 мм. Характер изменений соответствует картине рассеянного склероза. Атрофических изменений не выявлено.',
    createdAt: '2024-01-10T14:20:00Z',
    status: 'completed',
    anomalies: ['Демиелинизация'],
    confidence: 87,
    recommendations: ['Консультация невролога', 'Исследование на олигоклональные антитела']
  },
  {
    id: '3',
    inputImage: 'img/1.jpg',
    outputImage: 'img/2.jpg',
    description: 'В левой лобной доле определяется ишемический очаг размером 1.5×1.2 см. Отмечается снижение МР-сигнала на Т1 и повышение на Т2. Признаков масс-эффекта нет. Проходимость магистральных артерий сохранена.',
    createdAt: '2024-01-05T09:15:00Z',
    status: 'completed',
    anomalies: ['Ишемический очаг'],
    confidence: 95,
    recommendations: ['УЗДГ БЦА', 'Консультация сосудистого хирурга']
  },
  {
    id: '4',
    inputImage: 'img/1.jpg',
    outputImage: 'img/2.jpg',
    description: 'Обнаружена аневризма левой средней мозговой артерии размером 7×5 мм. Форма мешотчатая, шейка узкая. Признаков разрыва или вазоспазма не выявлено. Остальные сосуды без особенностей.',
    createdAt: '2023-12-28T16:45:00Z',
    status: 'completed',
    anomalies: ['Аневризма'],
    confidence: 89,
    recommendations: ['Церебральная ангиография', 'Консультация нейрохирурга']
  },
  {
    id: '5',
    inputImage: 'img/1.jpg',
    outputImage: 'img/2.jpg',
    description: 'Определяется киста шишковидной железы размером 8×6 мм. Контуры чёткие, содержимое однородное. Окружающие структуры не сдавлены. Эпифиз обычной формы и размеров.',
    createdAt: '2023-12-20T11:10:00Z',
    status: 'completed',
    anomalies: ['Киста'],
    confidence: 85,
    recommendations: ['Повторное МРТ через 6 месяцев', 'Контроль гормонального фона']
  },
  {
    id: '6',
    inputImage: 'img/1.jpg',
    outputImage: 'img/2.jpg',
    description: 'На серии МРТ снимков патологических изменений не выявлено. Структуры головного мозга симметричны, желудочковая система не расширена, очаговых изменений МР-сигнала нет.',
    createdAt: '2023-12-15T13:30:00Z',
    status: 'completed',
    anomalies: [],
    confidence: 98,
    recommendations: ['Профилактическое обследование через год']
  },
  {
    id: '7',
    inputImage: 'img/1.jpg',
    outputImage: 'img/2.jpg',
    description: 'Выявлены признаки лейкоареоза вокруг передних рогов боковых желудочков. Умеренная церебральная атрофия. Микроангиопатия. Острых очаговых изменений не обнаружено.',
    createdAt: '2023-12-10T10:00:00Z',
    status: 'completed',
    anomalies: ['Лейкоареоз', 'Церебральная атрофия'],
    confidence: 82,
    recommendations: ['Контроль АД', 'Нейропротективная терапия']
  },
  {
    id: '8',
    inputImage: 'img/1.jpg',
    outputImage: 'img/2.jpg',
    description: 'Обнаружена менингиома правой теменной области размером 2.1×1.9 см с выраженным перитуморальным отёком. Образование интенсивно накапливает контраст. Отмечается умеренный масс-эффект.',
    createdAt: '2023-12-05T15:45:00Z',
    status: 'completed',
    anomalies: ['Менингиома', 'Отёк'],
    confidence: 94,
    recommendations: ['Хирургическое лечение', 'Консультация нейроонколога']
  },
  {
    id: '9',
    inputImage: 'https://picsum.photos/seed/mri9/400/400',
    outputImage: 'https://picsum.photos/seed/mri9-processed/400/400',
    description: 'В правой затылочной доле определяется геморрагический очаг размером 1.8×1.5 см. По периферии зона гемосидерина. Признаков продолженного роста нет. Сосуды Дорелло без особенностей.',
    createdAt: '2023-11-28T12:20:00Z',
    status: 'completed',
    anomalies: ['Геморрагический очаг'],
    confidence: 91,
    recommendations: ['Коагулограмма', 'Исключение сосудистых мальформаций']
  },
  {
    id: '10',
    inputImage: 'https://picsum.photos/seed/mri10/400/400',
    outputImage: 'https://picsum.photos/seed/mri10-processed/400/400',
    description: 'МР-картина соответствует нормотипическому варианту строения головного мозга. Патологических изменений не выявлено. Все структуры дифференцируются чётко, очаговых изменений нет.',
    createdAt: '2023-11-20T09:30:00Z',
    status: 'completed',
    anomalies: [],
    confidence: 97,
    recommendations: ['Плановое обследование через 2 года']
  },
  {
    id: '11',
    inputImage: 'https://picsum.photos/seed/mri11/400/400',
    outputImage: 'https://picsum.photos/seed/mri11-processed/400/400',
    description: 'Обнаружена артерио-венозная мальформация в левой теменной доле размером 1.9×1.6 см. Отмечается характерная картина "клубка" сосудов. Признаков кровоизлияния нет.',
    createdAt: '2023-11-15T14:10:00Z',
    status: 'completed',
    anomalies: ['АВМ'],
    confidence: 88,
    recommendations: ['Церебральная ангиография', 'Радиохирургическое лечение']
  },
  {
    id: '12',
    inputImage: 'https://picsum.photos/seed/mri12/400/400',
    outputImage: 'https://picsum.photos/seed/mri12-processed/400/400',
    description: 'Обработка изображения...',
    createdAt: '2024-01-18T16:30:00Z',
    status: 'processing',
    anomalies: [],
    confidence: 0
  },
  {
    id: '13',
    inputImage: 'https://picsum.photos/seed/mri13/400/400',
    outputImage: '',
    description: '',
    createdAt: '2024-01-19T10:00:00Z',
    status: 'pending',
    anomalies: []
  }
]