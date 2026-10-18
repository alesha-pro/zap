# Сборки и релизы alesha-pro/zap

## Проверки изменений

`CI` запускается на pull request и при обновлении `master`. Он проверяет YAML
через закреплённый actionlint, проверяет валидатор релизных файлов и выполняет
`cargo check --locked` с релизными features на Linux, macOS ARM64/Intel и Windows.
Проверки PR имеют только `contents: read`, включая PR из чужих форков.

## Проверить полную сборку

```sh
gh workflow run zap_release.yml --repo alesha-pro/zap --ref master -f mode=build
gh run list --repo alesha-pro/zap --workflow zap_release.yml
```

Этот режим создаёт Actions artifacts без создания тега или GitHub Release.
Все платформы собираются из одного SHA; версия указана в summary запуска.
После успешной проверки пакеты доступны в artifacts `zap-*`, а манифест
и контрольные суммы — в `release-verification`. Проверочный запуск хранит
artifacts 7 дней. После успешной загрузки в Release промежуточные artifacts
удаляются; пакеты Release хранятся отдельно.

## Выпустить версию

Формат версии: `vYYYY.MM.DD.N`, например `v2026.10.18.1`.
Последний компонент — возрастающий номер в пределах дня. Он совместим с
сравнением версий в автообновлении ZAP. Для выпуска используйте новый тег
на проверенном коммите `master`:

```sh
git fetch origin
git tag v2026.10.18.1 origin/master
git push origin v2026.10.18.1
```

Push тега запускает сборки. Workflow проверяет принадлежность коммита основной
ветке, собирает все обязательные пакеты, проверяет комплект и записывает
`SHA256SUMS` и `BUILD_INFO.json`. Только после этого создаётся черновик Release,
загружаются файлы и Release становится публичным и `latest`.
Если загрузка прервалась, черновик остаётся для диагностики; перед повторным
выпуском удалите неудачный черновик либо выберите новую версию. Готовые Releases
автоматически не перезаписываются.

Можно получить только черновик, не меняя источник автообновления `latest`:

```sh
gh workflow run zap_release.yml --repo alesha-pro/zap --ref master \
  -f mode=draft -f tag=v2026.10.18.1
```

Имя версии можно опустить: ручной запуск использует дату UTC и номер workflow
run. Перед публикацией черновика проверьте его пакеты; публикация выполняется
через GitHub Releases или `gh release edit TAG --draft=false --latest`.

## Пакеты и подписи

Обязательные файлы: macOS ARM64/Intel DMG, Windows x64 installer, Linux x86_64
AppImage и DEB, три CLI tarball (macOS ARM64/Intel, Linux x86_64).
RPM и Arch packages собираются дополнительно; их отсутствие не блокирует релиз.
Linux GUI требует glibc 2.35 или новее; Linux CLI использует static musl.

macOS использует ad-hoc подпись без notarization; Windows installer не подписан.
Для Apple Developer ID/notarization нужны отдельные сертификат и учётные данные
Apple. GitHub-токен их не заменяет. Эти credentials пока не настроены.

Для текущего workflow дополнительных Secrets, PAT или SSH-ключей не нужно.
GitHub выдаёт `GITHUB_TOKEN` каждому запуску; `contents: write` и `actions: write` получает только
job публикации (второе право — для удаления промежуточных artifacts своего запуска). Личный токен `gh` не копируется в репозиторий или Actions.
Стандартные публичные GitHub-hosted runners используются без платных larger
runners. Подготовка macOS не зависит от Homebrew: protoc 25.1 закреплён
SHA-256, create-dmg 1.3.0 — SHA коммита. Автообновление приложения и remote-server обращаются к Releases
`alesha-pro/zap`.
