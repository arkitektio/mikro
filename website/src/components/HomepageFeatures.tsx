import useBaseUrl from "@docusaurus/useBaseUrl";
import React from "react";
import clsx from "clsx";
import styles from "./HomepageFeatures.module.css";

type FeatureItem = {
  title: string;
  image: string;
  description: JSX.Element;
};

const FeatureList: FeatureItem[] = [
  {
    title: "GraphQL API",
    image: "/img/undraw_docusaurus_mountain.svg",
    description: (
      <>
        mikro is a GraphQL API that allows you to query and update your
        Microscopy data in a simple and intuitive way. With GraphQL managing
        data becomes a breeze and managing your data is no longer a challenge.
      </>
    ),
  },
  {
    title: "Pydantic",
    image: "/img/undraw_docusaurus_tree.svg",
    description: (
      <>
        mikro integrates well with pydantic and gives you sensible and fully
        typed apis
      </>
    ),
  },
  {
    title: "Async ready",
    image: "/img/undraw_docusaurus_react.svg",
    description: (
      <>
        mikro is async ready and provides a synchronous and asynchronous api, so
        that you can choose your style and opt in for performance when you want
        to
      </>
    ),
  },
];

function Feature({ title, image, description }: FeatureItem) {
  return (
    <div className={clsx("col col--4")}>
      <div className="text--center padding-horiz--md padding-top--md">
        <h3>{title}</h3>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default function HomepageFeatures(): JSX.Element {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}
