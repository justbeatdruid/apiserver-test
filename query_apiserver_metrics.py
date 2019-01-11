import requests

prometheusServerAddr = "http://10.196.131.93:80"
prometheusQueryApi = "/api/v1/query"

class Query:
    def __init__(self, resource, verbs, scope):
        # type: verbs: [string]
        # type: scope: string
        self.resource = resource
        self.verbs = verbs
        self.scope = scope

    def getQueryStatement(self):
        res = []
        for verb in self.verbs:
            res.append('apiserver_request_latencies_summary{resource="%s",scope="%s",verb="%s"}' % (self.resource, self.scope, verb))
        return res

    def getMetrics(self):
        res = {}
        for query in self.getQueryStatement():
            response = requests.get(prometheusServerAddr+prometheusQueryApi, params={"query":query})
            response.raise_for_status()
            for result in response.json()["data"]["result"]:
                value = result["value"][1]
                quantile, verb = result["metric"]["quantile"], result["metric"]["verb"]
                if not res.has_key(quantile):
                    res[quantile] = {}
                res[quantile][verb] = float(value) / 1000.0
        return res

    def getName(self):
        return self.resource.upper()

defaultVerbs = ["GET","LIST","POST","PUT","DELETE"]

def printCsv(metrics):
    headline = ""
    lines = ""
    for q in metrics:
        m = metrics[q]
        head, values = [], []
        hform, form = "{:<10}", "{:<10}"
        for vb in m:
            head.append(vb)
            values.append(m[vb])
            hform += "{:<10} "
            form += "{:<10.3f} "
        headline = hform.format("", *head) + "\n"
        lines += form.format(q, *values) + "\n"
    return headline + lines

def main():
    endpoint = Query("endpoints", defaultVerbs, "namespace")
    event = Query("events", defaultVerbs, "namespace")
    node = Query("nodes", defaultVerbs, "cluster")
    pod = Query("pods", defaultVerbs, "namespace")
    quota = Query("resourcequotas", defaultVerbs, "namespace")
    service = Query("services", defaultVerbs, "namespace")
    resources = [endpoint, event, node, pod, quota, service, ]
    for r in resources:
        print r.getName()
        print printCsv(r.getMetrics())

if __name__ == '__main__':
    main()
