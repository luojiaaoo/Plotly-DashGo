import re
import dash

cdn_modules = [
    'DashRenderer',
    'dash_html_components',
    'dash_core_components',
    'feffery_antd_components',
    'feffery_utils_components',
    'feffery_markdown_components',
]


class CustomDash(dash.Dash):
    """
    自定义Dash实例，用于改造默认的CDN访问行为
    """

    def interpolate_index(self, **kwargs):
        scripts = kwargs.pop('scripts')

        # 提取scripts部分符合条件的外部js资源
        external_scripts = re.findall('(<script src="http.*?"></script>)', scripts)

        # 将原有的script标签内容替换为带备用地址错误切换的版本
        for external_script in external_scripts:
            # 提取当前资源地址
            origin_script_src = re.findall('"(.*?)"', external_script)[0]
            # 抽取关键信息
            library_name, library_version, library_file = re.findall(
                'com/(.+)@(.+?)/(.+?)$', origin_script_src
            )[0]
            # 基于阿里cdn构建新的资源地址
            new_library_src = (
                f'https://registry.npmmirror.com/{library_name}/{library_version}/files/{library_file}'
            )

            scripts = scripts.replace(
                external_script,
                """<script src="{}" onerror='this.remove(); let fallbackScript = document.createElement("script"); fallbackScript.src = "{}"; document.querySelector("head").prepend(fallbackScript);'></script>""".format(
                    re.findall('"(.*?)"', external_script)[0].replace(
                        origin_script_src,
                        new_library_src,
                    ),
                    re.findall('"(.*?)"', external_script)[0],
                ),
            )

        scripts = (
            """
<script>
const requiredModules = {};
{}
</script>
""".format(
                str(cdn_modules),
                """// 自定义延时
const delay = (ms) => {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// 判断指定的多个模块是否均已加载
const areModulesLoaded = (modules) => {
    return modules.every(module => window[module]);
}

const waitForModules = async () => {
    while (!areModulesDefined(requiredModules)) {
        await delay(100); // 延迟100毫秒
    }

    // 若相关模块均已加载完成，手动初始化DashRenderer
    var renderer = new DashRenderer();
}

const customOnError = async (message, source, lineno, colno, error) => {
    if (message.includes('is not defined') !== -1) {
        await waitForModules();
    }
}

window.onerror = customOnError""",
            )
            + scripts
        )

        return super(CustomDash, self).interpolate_index(scripts=scripts, **kwargs)
